# gta_live_blur_dxdup_overlay_center_wipe.py
# Live-Backdrop-Overlay: DXGI Desktop Duplication (dxcam) + GLSL (Grayscale+Blur),
# click-through, WDA_EXCLUDEFROMCAPTURE, ESC beendet, F10 toggelt Sichtbarkeit.
# Effekt startet in der Mitte und breitet sich radial nach außen aus.

import sys, ctypes, time, numpy as np, dxcam
from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL
from OpenGL.GL import *

VERT = """
#version 330
layout(location=0) in vec2 in_pos;
layout(location=1) in vec2 in_uv;
out vec2 v_uv;
void main(){ v_uv=in_uv; gl_Position=vec4(in_pos,0.0,1.0); }
"""

FRAG_GRAY = """
#version 330
in vec2 v_uv; out vec4 frag; uniform sampler2D tex0;
void main(){ vec3 c=texture(tex0,v_uv).rgb; float g=dot(c, vec3(0.299,0.587,0.114)); frag=vec4(vec3(g),1.0); }
"""

FRAG_BLUR_H = """
#version 330
in vec2 v_uv; out vec4 frag; uniform sampler2D tex0; uniform float texelSize; uniform int kernelSize; uniform float sigma;
float gauss(float x,float s){return exp(-(x*x)/(2.0*s*s));}
void main(){ int r=kernelSize/2; vec3 sum=vec3(0); float wsum=0;
  for(int i=-r;i<=r;i++){ float w=gauss(i,sigma); sum+=texture(tex0, v_uv + vec2(i*texelSize,0)).rgb*w; wsum+=w; }
  frag=vec4(sum/wsum,1.0);
}
"""

FRAG_BLUR_V = """
#version 330
in vec2 v_uv; out vec4 frag; uniform sampler2D tex0; uniform float texelSize; uniform int kernelSize; uniform float sigma;
float gauss(float x,float s){return exp(-(x*x)/(2.0*s*s));}
void main(){ int r=kernelSize/2; vec3 sum=vec3(0); float wsum=0;
  for(int i=-r;i<=r;i++){ float w=gauss(i,sigma); sum+=texture(tex0, v_uv + vec2(0, i*texelSize)).rgb*w; wsum+=w; }
  frag=vec4(sum/wsum,1.0);
}
"""

# Mischt Original (tex_orig) und Blur (tex_blur) anhand eines radialen, wachsenden Radius.
FRAG_COMPOSITE = """
#version 330
in vec2 v_uv; out vec4 frag;
uniform sampler2D tex_orig;
uniform sampler2D tex_blur;
uniform float u_radius;    // 0..~1.5 (normierter Halbmesser)
uniform float u_softness;  // weiche Kante, z.B. 0.05
uniform vec2  u_aspect;    // (width,height)

void main(){
    // uv -> -1..1 Raum mit Aspect-Korrektur, damit der Kreis nicht oval wird
    vec2 uv = v_uv * 2.0 - 1.0;
    uv.x *= u_aspect.x / u_aspect.y;
    float d = length(uv); // Abstand zur Mitte

    // weiche Übergangsmaske (0 = Original innen, 1 = Blur außen oder umgekehrt)
    float t = smoothstep(u_radius - u_softness, u_radius + u_softness, d);

    vec3 c_orig = texture(tex_orig, v_uv).rgb;
    vec3 c_blur = texture(tex_blur, v_uv).rgb;

    // Effekt breitet sich von innen nach außen aus:
    // innen (d < u_radius) => Blur; außen => Original
    vec3 c = mix(c_blur, c_orig, t);
    frag = vec4(c, 1.0);
}
"""

def compile_prog(vs_src, fs_src):
    vs=glCreateShader(GL_VERTEX_SHADER); glShaderSource(vs,vs_src); glCompileShader(vs)
    if glGetShaderiv(vs, GL_COMPILER_SINCE)!=GL_TRUE and glGetShaderiv(vs, GL_COMPILE_STATUS)!=GL_TRUE:
        raise RuntimeError(glGetShaderInfoLog(vs).decode())
    fs=glCreateShader(GL_FRAGMENT_SHADER); glShaderSource(fs,fs_src); glCompileShader(fs)
    if glGetShaderiv(fs, GL_COMPILE_STATUS)!=GL_TRUE:
        raise RuntimeError(glGetShaderInfoLog(fs).decode())
    p=glCreateProgram(); glAttachShader(p,vs); glAttachShader(p,fs); glLinkProgram(p)
    if glGetProgramiv(p, GL_LINK_STATUS)!=GL_TRUE: raise RuntimeError(glGetProgramInfoLog(p).decode())
    glDeleteShader(vs); glDeleteShader(fs); return p

class GLView(QtOpenGL.QGLWidget):
    def __init__(self, parent=None, output_idx=0, region=None):
        fmt = QtOpenGL.QGLFormat()
        fmt.setSwapInterval(0)
        super().__init__(fmt, parent)
        self.setAutoFillBackground(False)

        # Blur/Look
        self.kernel=21; self.sigma=8.0; self.darken=0.25

        # Radial-Wipe-Params
        self.softness = 0.06     # weiche Kante des Rings
        self.wipe_speed = 0.35   # Radius-Wachstum pro Sekunde (in "normierten" Einheiten)
        self.radius = 0.0        # startet bei 0
        self._last_time = time.perf_counter()

        self.output_idx = output_idx
        self.cam = dxcam.create(output_idx=output_idx, output_color="RGB")
        self.region = region
        m = self.cam.outputs[output_idx]
        self.W, self.H = (m["width"], m["height"])
        self._tex_src = None

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(0)

    def sizeHint(self):
        return QtCore.QSize(self.W, self.H)

    def initializeGL(self):
        glDisable(GL_DEPTH_TEST)
        self.prog_gray = compile_prog(VERT, FRAG_GRAY)
        self.prog_h    = compile_prog(VERT, FRAG_BLUR_H)
        self.prog_v    = compile_prog(VERT, FRAG_BLUR_V)
        self.prog_comp = compile_prog(VERT, FRAG_COMPOSITE)

        quad = np.array([
            -1.0,-1.0, 0.0,0.0,
             1.0,-1.0, 1.0,0.0,
             1.0, 1.0, 1.0,1.0,
            -1.0, 1.0, 0.0,1.0,
        ], dtype=np.float32)
        idx = np.array([0,1,2,0,2,3], dtype=np.uint32)
        self.vao=glGenVertexArrays(1); glBindVertexArray(self.vao)
        self.vbo=glGenBuffers(1); glBindBuffer(GL_ARRAY_BUFFER,self.vbo); glBufferData(GL_ARRAY_BUFFER, quad.nbytes, quad, GL_STATIC_DRAW)
        self.ebo=glGenBuffers(1); glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,self.ebo); glBufferData(GL_ELEMENT_ARRAY_BUFFER, idx.nbytes, idx, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0); glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,16,ctypes.c_void_p(0))
        glEnableVertexAttribArray(1); glVertexAttribPointer(1,2,GL_FLOAT,GL_FALSE,16,ctypes.c_void_p(8))
        glBindVertexArray(0)

        # Texturen/FBOs
        def mktex(w,h):
            t=glGenTextures(1); glBindTexture(GL_TEXTURE_2D,t)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexImage2D(GL_TEXTURE_2D,0,GL_RGB,w,h,0,GL_RGB,GL_UNSIGNED_BYTE,None)
            glBindTexture(GL_TEXTURE_2D,0); return t
        def mkfbo(w,h):
            f=glGenFramebuffers(1); t=mktex(w,h)
            glBindFramebuffer(GL_FRAMEBUFFER,f)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, t, 0)
            assert glCheckFramebufferStatus(GL_FRAMEBUFFER)==GL_FRAMEBUFFER_COMPLETE
            glBindFramebuffer(GL_FRAMEBUFFER,0); return f,t

        self._tex_src = mktex(self.W,self.H)
        self.fbo_gray, self.tex_gray = mkfbo(self.W,self.H)
        self.fbo_tmp,  self.tex_tmp  = mkfbo(self.W,self.H)
        self.fbo_blur, self.tex_blur = mkfbo(self.W,self.H)  # final blurred result

        self.cam.start(target_fps=60, video_mode=False)

    def _update_radius(self):
        now = time.perf_counter()
        dt = now - self._last_time
        self._last_time = now
        # radius bis max ~1.2 (über die Ecken hinaus) wachsen lassen
        self.radius = min(self.radius + self.wipe_speed * dt, 1.2)

    def paintGL(self):
        self._update_radius()

        frame = self.cam.get_latest_frame()
        if frame is None:
            return
        if self.region:
            l,t,r,b = self.region
            frame = frame[t:b, l:r]
        if frame.shape[1] != self.W or frame.shape[0] != self.H:
            frame = np.ascontiguousarray(
                np.array(QtGui.QImage(frame.data, frame.shape[1], frame.shape[0], 3*frame.shape[1], QtGui.QImage.Format_RGB888)
                ).scaled(self.W, self.H, QtCore.Qt.IgnoreAspectRatio).bits().asstring(self.W*self.H*3), dtype=np.uint8
            ).reshape(self.H, self.W, 3)

        glBindTexture(GL_TEXTURE_2D, self._tex_src)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.W, self.H, GL_RGB, GL_UNSIGNED_BYTE, frame)
        glBindTexture(GL_TEXTURE_2D, 0)

        glViewport(0,0,self.width(), self.height())

        # 1) Gray in tex_gray
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_gray)
        glUseProgram(self.prog_gray)
        glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, self._tex_src)
        glUniform1i(glGetUniformLocation(self.prog_gray,"tex0"),0)
        glBindVertexArray(self.vao); glDrawElements(GL_TRIANGLES,6,GL_UNSIGNED_INT,None)

        # 2) Blur H: tex_gray -> tex_tmp
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_tmp)
        glUseProgram(self.prog_h)
        glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, self.tex_gray)
        glUniform1i(glGetUniformLocation(self.prog_h,"tex0"),0)
        glUniform1f(glGetUniformLocation(self.prog_h,"texelSize"), 1.0/float(self.W))
        glUniform1i(glGetUniformLocation(self.prog_h,"kernelSize"), self.kernel)
        glUniform1f(glGetUniformLocation(self.prog_h,"sigma"), self.sigma)
        glDrawElements(GL_TRIANGLES,6,GL_UNSIGNED_INT,None)

        # 3) Blur V: tex_tmp -> tex_blur
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_blur)
        glUseProgram(self.prog_v)
        glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, self.tex_tmp)
        glUniform1i(glGetUniformLocation(self.prog_v,"tex0"),0)
        glUniform1f(glGetUniformLocation(self.prog_v,"texelSize"), 1.0/float(self.H))
        glUniform1i(glGetUniformLocation(self.prog_v,"kernelSize"), self.kernel)
        glUniform1f(glGetUniformLocation(self.prog_v,"sigma"), self.sigma)
        glBindVertexArray(self.vao); glDrawElements(GL_TRIANGLES,6,GL_UNSIGNED_INT,None)

        # 4) Composite (Radial-Wipe) -> Backbuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glUseProgram(self.prog_comp)
        glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, self._tex_src)
        glUniform1i(glGetUniformLocation(self.prog_comp,"tex_orig"),0)
        glActiveTexture(GL_TEXTURE1); glBindTexture(GL_TEXTURE_2D, self.tex_blur)
        glUniform1i(glGetUniformLocation(self.prog_comp,"tex_blur"),1)
        # Aspect (für kreisrunde Maske)
        glUniform2f(glGetUniformLocation(self.prog_comp,"u_aspect"), float(self.width()), float(self.height()))
        glUniform1f(glGetUniformLocation(self.prog_comp,"u_radius"), self.radius)
        glUniform1f(glGetUniformLocation(self.prog_comp,"u_softness"), self.softness)
        glBindVertexArray(self.vao); glDrawElements(GL_TRIANGLES,6,GL_UNSIGNED_INT,None)

        # 5) Abdunkeln
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glUseProgram(0)
        glBegin(GL_TRIANGLES)
        glColor4f(0,0,0,self.darken)
        glVertex2f(-1,-1); glVertex2f(1,-1); glVertex2f(1,1)
        glVertex2f(-1,-1); glVertex2f(1,1);  glVertex2f(-1,1)
        glEnd()
        glDisable(GL_BLEND)

    def closeEvent(self, e):
        try:
            self.cam.stop()
        except Exception:
            pass
        super().closeEvent(e)

class Overlay(QtWidgets.QWidget):
    def __init__(self, output_idx=0, region=None):
        super().__init__(None, QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setWindowFlag(QtCore.Qt.WindowDoesNotAcceptFocus, True)

        app = QtWidgets.QApplication.instance()
        geo = app.desktop().screenGeometry()
        self.setGeometry(geo)

        self.gl = GLView(self, output_idx=output_idx, region=region)
        self.gl.setGeometry(self.rect())

        self.shortcut_toggle = QtWidgets.QShortcut(QtGui.QKeySequence("F10"), self, activated=self.toggle_visible)
        app.installEventFilter(self)

        self._apply_exstyles_and_exclude_from_capture()

    def _apply_exstyles_and_exclude_from_capture(self):
        hwnd = self.winId().__int__()
        user32 = ctypes.windll.user32
        GetWindowLong = user32.GetWindowLongW
        SetWindowLong = user32.SetWindowLongW

        GWL_EXSTYLE = -20
        WS_EX_TRANSPARENT   = 0x00000020
        WS_EX_LAYERED       = 0x00080000
        WS_EX_TOOLWINDOW    = 0x00000080
        WS_EX_NOACTIVATE    = 0x08000000

        ex = GetWindowLong(hwnd, GWL_EXSTYLE)
        ex |= (WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
        SetWindowLong(hwnd, GWL_EXSTYLE, ex)

        WDA_EXCLUDEFROMCAPTURE = 0x11
        user32.SetWindowDisplayAffinity(ctypes.wintypes.HWND(hwnd), WDA_EXCLUDEFROMCAPTURE)

    def eventFilter(self, obj, ev):
        if isinstance(ev, QtGui.QKeyEvent) and ev.key()==QtCore.Qt.Key_Escape and ev.type()==QtCore.QEvent.KeyPress:
            QtWidgets.QApplication.quit()
            return True
        return super().eventFilter(obj, ev)

    def toggle_visible(self):
        self.setVisible(not self.isVisible())

    def showEvent(self, e):
        self.gl.setGeometry(self.rect())
        super().showEvent(e)

def main():
    app = QtWidgets.QApplication(sys.argv)
    ov = Overlay(output_idx=0)
    ov.showFullScreen()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
