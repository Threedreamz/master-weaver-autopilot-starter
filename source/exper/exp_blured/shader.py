# gta_live_blur_dxdup_overlay.py
# Live-Backdrop-Overlay: DXGI Desktop Duplication (dxcam) + GLSL (Grayscale+Blur),
# nicht-aktivierbar + click-through, und via WDA_EXCLUDEFROMCAPTURE vom Capture ausgeschlossen.
# ESC beendet, F10 toggelt Sichtbarkeit.

import sys, ctypes, numpy as np, dxcam
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

def compile_prog(vs_src, fs_src):
    vs=glCreateShader(GL_VERTEX_SHADER); glShaderSource(vs,vs_src); glCompileShader(vs)
    if glGetShaderiv(vs, GL_COMPILE_STATUS)!=GL_TRUE: raise RuntimeError(glGetShaderInfoLog(vs).decode())
    fs=glCreateShader(GL_FRAGMENT_SHADER); glShaderSource(fs,fs_src); glCompileShader(fs)
    if glGetShaderiv(fs, GL_COMPILE_STATUS)!=GL_TRUE: raise RuntimeError(glGetShaderInfoLog(fs).decode())
    p=glCreateProgram(); glAttachShader(p,vs); glAttachShader(p,fs); glLinkProgram(p)
    if glGetProgramiv(p, GL_LINK_STATUS)!=GL_TRUE: raise RuntimeError(glGetProgramInfoLog(p).decode())
    glDeleteShader(vs); glDeleteShader(fs); return p

class GLView(QtOpenGL.QGLWidget):
    def __init__(self, parent=None, output_idx=0, region=None):
        fmt = QtOpenGL.QGLFormat()
        fmt.setSwapInterval(0)
        super().__init__(fmt, parent)
        self.setAutoFillBackground(False)
        self.kernel=21; self.sigma=8.0; self.darken=0.25
        self.output_idx = output_idx
        # DXGI Desktop Duplication
        self.cam = dxcam.create(output_idx=output_idx, output_color="RGB")
        # region=None -> gesamter Output; sonst (left, top, right, bottom)
        self.region = region
        m = self.cam.outputs[output_idx]
        self.W, self.H = (m["width"], m["height"])
        self._tex_src = None

        # Timer für ~max FPS (dxcam ist schnell; wir lassen Qt treiben)
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

        # dxcam starten
        self.cam.start(target_fps=60, video_mode=False)

    def paintGL(self):
        # 1) aktuellen Desktopframe holen (ohne unser Overlay dank WDA_EXCLUDEFROMCAPTURE)
        frame = self.cam.get_latest_frame()
        if frame is None:
            return
        if self.region:
            l,t,r,b = self.region
            frame = frame[t:b, l:r]
        # Sicherheits-reshape auf erwartete Größe
        if frame.shape[1] != self.W or frame.shape[0] != self.H:
            # skaliere auf Fenstergröße für konstanten Blur
            frame = np.ascontiguousarray(
                np.array(QtGui.QImage(frame.data, frame.shape[1], frame.shape[0], 3*frame.shape[1], QtGui.QImage.Format_RGB888)
                ).scaled(self.W, self.H, QtCore.Qt.IgnoreAspectRatio).bits().asstring(self.W*self.H*3), dtype=np.uint8
            ).reshape(self.H, self.W, 3)

        glBindTexture(GL_TEXTURE_2D, self._tex_src)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.W, self.H, GL_RGB, GL_UNSIGNED_BYTE, frame)
        glBindTexture(GL_TEXTURE_2D, 0)

        glViewport(0,0,self.width(), self.height())

        # 2) Gray
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_gray)
        glUseProgram(self.prog_gray)
        glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, self._tex_src)
        glUniform1i(glGetUniformLocation(self.prog_gray,"tex0"),0)
        glBindVertexArray(self.vao); glDrawElements(GL_TRIANGLES,6,GL_UNSIGNED_INT,None)

        # 3) Blur H
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_tmp)
        glUseProgram(self.prog_h)
        glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, self.tex_gray)
        glUniform1i(glGetUniformLocation(self.prog_h,"tex0"),0)
        glUniform1f(glGetUniformLocation(self.prog_h,"texelSize"), 1.0/float(self.W))
        glUniform1i(glGetUniformLocation(self.prog_h,"kernelSize"), self.kernel)
        glUniform1f(glGetUniformLocation(self.prog_h,"sigma"), self.sigma)
        glDrawElements(GL_TRIANGLES,6,GL_UNSIGNED_INT,None)

        # 4) Blur V -> Backbuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glUseProgram(self.prog_v)
        glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, self.tex_tmp)
        glUniform1i(glGetUniformLocation(self.prog_v,"tex0"),0)
        glUniform1f(glGetUniformLocation(self.prog_v,"texelSize"), 1.0/float(self.H))
        glUniform1i(glGetUniformLocation(self.prog_v,"kernelSize"), self.kernel)
        glUniform1f(glGetUniformLocation(self.prog_v,"sigma"), self.sigma)
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
        # nicht-aktivierbar & click-through
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setWindowFlag(QtCore.Qt.WindowDoesNotAcceptFocus, True)

        # Vollbild auf ausgewähltem Output
        app = QtWidgets.QApplication.instance()
        geo = app.desktop().screenGeometry()  # virtueller Desktop; für Multi-Monitore ggf. pro-Monitor-Geo holen
        self.setGeometry(geo)

        self.gl = GLView(self, output_idx=output_idx, region=region)
        self.gl.setGeometry(self.rect())

        # ESC / F10
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

        # Exclude from screen/window capture (Win10 2004+)
        WDA_EXCLUDEFROMCAPTURE = 0x11
        user32.SetWindowDisplayAffinity(ctypes.wintypes.HWND(hwnd), WDA_EXCLUDEFROMCAPTURE)

    def eventFilter(self, obj, ev):
        if isinstance(ev, QtGui.QKeyEvent) and ev.key()==QtCore.Qt.Key_Escape and ev.type()==QtCore.QEvent.KeyPress:
            QtWidgets.QApplication.quit()
            return True
        return super().eventFilter(obj, ev)

    def toggle_visible(self):
        self.setVisible(not self.isVisible())  # small trick; toggled by F10

    def showEvent(self, e):
        self.gl.setGeometry(self.rect())
        super().showEvent(e)

def main():
    app = QtWidgets.QApplication(sys.argv)
    ov = Overlay(output_idx=0)  # 0 = primärer Output; bei Multi-Monitoren ggf. anpassen
    ov.showFullScreen()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
