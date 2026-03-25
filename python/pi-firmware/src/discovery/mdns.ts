import Bonjour, { type Service } from "bonjour-service";

const SERVICE_TYPE = "autopilot-pi";
const SERVICE_NAME = "autopilot-pi-camera";
const VERSION = "0.1.0";

export class MdnsService {
  private bonjour: InstanceType<typeof Bonjour>;
  private service: Service | null = null;
  private port: number;
  private cameraCount: number;
  private browser: ReturnType<InstanceType<typeof Bonjour>["find"]> | null = null;
  private discoveredServices: Array<{ name: string; host: string; port: number; txt: Record<string, string> }> = [];

  constructor(port: number, cameraCount: number) {
    this.bonjour = new Bonjour();
    this.port = port;
    this.cameraCount = cameraCount;
  }

  /**
   * Publish this Pi camera server on the local network via mDNS.
   */
  publish(): void {
    this.service = this.bonjour.publish({
      name: SERVICE_NAME,
      type: SERVICE_TYPE,
      port: this.port,
      protocol: "tcp",
      txt: {
        cameras: String(this.cameraCount),
        version: VERSION,
        platform: process.platform,
        arch: process.arch,
      },
    });

    console.log(`mDNS: Published _${SERVICE_TYPE}._tcp on port ${this.port}`);

    // Also discover other autopilot services on the network
    this.browser = this.bonjour.find({ type: SERVICE_TYPE }, (service) => {
      // Don't track our own service
      if (service.name === SERVICE_NAME && service.port === this.port) return;

      this.discoveredServices.push({
        name: service.name,
        host: service.host,
        port: service.port,
        txt: (service.txt ?? {}) as Record<string, string>,
      });

      console.log(`mDNS: Discovered peer service: ${service.name} at ${service.host}:${service.port}`);
    });
  }

  /**
   * Stop publishing and browsing.
   */
  unpublish(): void {
    if (this.service) {
      this.service.stop?.();
      this.service = null;
    }
    if (this.browser) {
      this.browser.stop();
      this.browser = null;
    }
    this.bonjour.destroy();
    console.log("mDNS: Service unpublished");
  }

  /**
   * Get list of discovered peer services.
   */
  getDiscoveredServices(): Array<{ name: string; host: string; port: number; txt: Record<string, string> }> {
    return [...this.discoveredServices];
  }
}
