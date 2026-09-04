import { Notice, Plugin, TFile } from 'obsidian';

type ProjectionManifest = {
  rendererId?: string;
  rendererVersion?: string;
  projectionAuthority?: string;
  roundTripCapability?: string;
  sources?: unknown[];
  outputs?: unknown[];
};

export default class DerivedProjectionPlugin extends Plugin {
  async onload(): Promise<void> {
    this.addCommand({
      id: 'projection-status',
      name: 'Show derived projection status',
      callback: () => { void this.showStatus(); },
    });

    this.addCommand({
      id: 'open-projection-home',
      name: 'Open derived projection home',
      callback: () => { void this.app.workspace.openLinkText('README.md', '', false); },
    });

    this.addCommand({
      id: 'open-repair-lineage',
      name: 'Open repair lineage canvas',
      callback: () => { void this.app.workspace.openLinkText('graphs/repair-lineage.canvas', '', false); },
    });
  }

  private async loadManifest(): Promise<ProjectionManifest | null> {
    const abstract = this.app.vault.getAbstractFileByPath('manifest.json');
    if (!(abstract instanceof TFile)) return null;
    const raw = await this.app.vault.cachedRead(abstract);
    try {
      return JSON.parse(raw) as ProjectionManifest;
    } catch {
      return null;
    }
  }

  private projectionLinkCount(): number {
    let count = 0;
    for (const file of this.app.vault.getMarkdownFiles()) {
      if (!file.path.startsWith('objects/')) continue;
      const cache = this.app.metadataCache.getFileCache(file);
      count += cache?.links?.length ?? 0;
    }
    return count;
  }

  private async showStatus(): Promise<void> {
    const manifest = await this.loadManifest();
    if (!manifest) {
      new Notice('No derived projection manifest found.');
      return;
    }
    if (manifest.projectionAuthority !== 'none' || manifest.roundTripCapability !== 'RENDER_ONLY') {
      new Notice('Projection authority contract is invalid. Treat this vault as untrusted.');
      return;
    }
    const objects = manifest.sources?.length ?? 0;
    const links = this.projectionLinkCount();
    new Notice(`Derived projection: ${objects} objects, ${links} indexed links. Authority: none.`);
  }
}
