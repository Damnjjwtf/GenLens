/**
 * lib/scraper/sources-deferred.ts
 *
 * Sources for verticals not yet active. Activate when survey trigger fires:
 *   motion_graphics:    15%+ of users self-identify as motion designers
 *   fashion:            20%+ of users self-identify as fashion designers
 *   music_production:   15%+ of users self-identify as music producers
 *
 * To activate: import the relevant array and append to SOURCES in sources.ts.
 */

import type { Source } from './sources'

export const DEFERRED_MOTION_GRAPHICS: Source[] = [
  { name: 'Motionographer', url: 'https://motionographer.com/feed/', type: 'rss', verticals: ['motion_graphics', 'filmmaking'], dimensions: [3, 9, 10], scrape_interval: 24 },
  { name: 'Stash Magazine', url: 'https://www.stashmedia.tv/feed/', type: 'rss', verticals: ['motion_graphics'], dimensions: [3, 9, 10], scrape_interval: 48 },
  { name: 'Greyscalegorilla', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UC64Z_7asrekIkc5h2v5tnHw', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 4, 5], scrape_interval: 48 },
  { name: 'School of Motion', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCAhdxqdrDN3gWJkaUFl9G-Q', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 4, 5, 7], scrape_interval: 48 },
  { name: 'r/AfterEffects', url: 'https://www.reddit.com/r/AfterEffects/.rss', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 4, 8], scrape_interval: 12 },
  { name: 'r/motiondesign', url: 'https://www.reddit.com/r/motiondesign/.rss', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 3, 9], scrape_interval: 12 },
  { name: 'Rive Blog', url: 'https://rive.app/blog/rss.xml', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 5, 8], scrape_interval: 48 },
  { name: 'Framer Blog', url: 'https://www.framer.com/blog/rss.xml', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 5], scrape_interval: 48 },
  { name: 'Spline Blog', url: 'https://spline.design/blog/rss.xml', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 5], scrape_interval: 48 },
  { name: 'Jitter Blog', url: 'https://jitter.video/blog/rss.xml', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 4, 5], scrape_interval: 48 },
  { name: 'Theatre.js', url: 'https://github.com/theatre-js/theatre/releases.atom', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 8], scrape_interval: 72 },
  { name: 'fxphd Blog', url: 'https://www.fxphd.com/fxblog/', type: 'html', verticals: ['motion_graphics', 'filmmaking'], dimensions: [1, 4], scrape_interval: 48 },
  { name: 'TouchDesigner Derivative Forum', url: 'https://forum.derivative.ca/posts.rss', type: 'rss', verticals: ['motion_graphics', 'filmmaking'], dimensions: [1, 8], scrape_interval: 12, notes: 'CHOP/SOP logic, Python integrations, interactive installation bugs' },
  { name: 'Okami Rufu (TouchDesigner)', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCnev7mI3HGGI', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 4], scrape_interval: 168, notes: 'Verify channel ID. Procedural geometry, GLSL shading' },
  { name: 'The Coding Train', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCvjgXvBlbQiydffZU7m1_aw', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 4], scrape_interval: 48, notes: 'Daniel Shiffman generative art, p5.js, ml5.js' },
  { name: 'SplineTool YouTube', url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UC8DeS2i81IY', type: 'rss', verticals: ['motion_graphics'], dimensions: [1], scrape_interval: 168, notes: 'Verify channel ID. Browser-based 3D motion design updates' },
  { name: 'Awesome Creative Coding (curated)', url: 'https://github.com/terkelg/awesome-creative-coding/commits/master.atom', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 8], scrape_interval: 168 },
  { name: 'py5 Library', url: 'https://github.com/py5coding/py5generator/commits/main.atom', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 8], scrape_interval: 168, notes: 'Processing in Python 3 with NumPy/Shapely' },
  { name: 'Konstrukt SVG Generator', url: 'https://github.com/MarcelMue/konstrukt/releases.atom', type: 'rss', verticals: ['motion_graphics'], dimensions: [1, 4], scrape_interval: 168 },
  { name: 'Eases Equations Library', url: 'https://github.com/mattdesl/eases/commits/master.atom', type: 'rss', verticals: ['motion_graphics'], dimensions: [4], scrape_interval: 168, notes: 'Robert Penner easing equations for procedural motion' },
]

export const DEFERRED_FASHION: Source[] = [
  { name: 'CLO Virtual Fashion Blog', url: 'https://www.clo3d.com/blog/feed/', type: 'rss', verticals: ['fashion'], dimensions: [1, 2, 5], scrape_interval: 48 },
  { name: 'Marvelous Designer Blog', url: 'https://www.marvelousdesigner.com/blog/feed/', type: 'rss', verticals: ['fashion'], dimensions: [1, 2], scrape_interval: 48 },
  { name: 'Browzwear Blog', url: 'https://browzwear.com/blog/feed/', type: 'rss', verticals: ['fashion'], dimensions: [1, 2, 5], scrape_interval: 48 },
  { name: 'Optitex Blog', url: 'https://optitex.com/blog/feed/', type: 'rss', verticals: ['fashion'], dimensions: [1, 2], scrape_interval: 48 },
  { name: 'Sourcing Journal', url: 'https://sourcingjournal.com/feed/', type: 'rss', verticals: ['fashion'], dimensions: [1, 2, 6], scrape_interval: 24 },
  { name: 'Business of Fashion Technology', url: 'https://www.businessoffashion.com/technology/feed/', type: 'rss', verticals: ['fashion'], dimensions: [1, 2, 5], scrape_interval: 24, notes: 'Verify RSS path — may need generator' },
  { name: 'Vogue Business Technology', url: 'https://www.voguebusiness.com/technology', type: 'html', verticals: ['fashion'], dimensions: [2, 9], scrape_interval: 48 },
  { name: 'r/clo3d', url: 'https://www.reddit.com/r/clo3d/.rss', type: 'rss', verticals: ['fashion', 'product_photography'], dimensions: [1, 2, 4], scrape_interval: 24 },
  { name: 'r/marvelousdesigner', url: 'https://www.reddit.com/r/marvelousdesigner/.rss', type: 'rss', verticals: ['fashion'], dimensions: [1, 2, 4], scrape_interval: 24 },
  { name: 'r/PatternMaking', url: 'https://www.reddit.com/r/PatternMaking/.rss', type: 'rss', verticals: ['fashion'], dimensions: [1, 4], scrape_interval: 24 },
  { name: 'Cool-GenAI-Fashion-Papers (curated)', url: 'https://github.com/wendashi/Cool-GenAI-Fashion-Papers/commits/main.atom', type: 'rss', verticals: ['fashion'], dimensions: [1, 5], scrape_interval: 168, notes: 'CVPR/SIGGRAPH papers on garment dynamics, virtual try-on' },
  { name: 'CLO 3D Notices (official)', url: 'https://www.clo3d.com/en/resources/notices/rss', type: 'rss', verticals: ['fashion'], dimensions: [1, 8], scrape_interval: 168, notes: 'Avatar rigging, fabric physics patches' },
  { name: 'Marvelous Designer User Spotlight', url: 'https://www.marvelousdesigner.com/userspotlight/rss', type: 'rss', verticals: ['fashion', 'filmmaking'], dimensions: [4], scrape_interval: 168, notes: 'Pattern makers bridging fashion + VFX costume work' },
  { name: 'Journal of Textile Science & Fashion Tech', url: 'https://irispublishers.com/jtsft/rss.xml', type: 'rss', verticals: ['fashion'], dimensions: [1, 5], scrape_interval: 168, notes: 'Academic: fiber science, sustainable material engineering' },
  { name: 'US Fashion Industry Association', url: 'https://www.usfashionindustry.com/feed', type: 'rss', verticals: ['fashion'], dimensions: [6, 8], scrape_interval: 168, notes: 'Regulatory + sourcing + trade policy' },
  { name: 'Fibre2Fashion Tech News', url: 'https://feeds.feedburner.com/fibre2fashion/technologynews', type: 'rss', verticals: ['fashion'], dimensions: [1, 8], scrape_interval: 24, notes: 'IoT + CAD-CAM + Industry 4.0 in textile mills' },
]

export const DEFERRED_MUSIC_PRODUCTION: Source[] = [
  { name: 'MusicTech', url: 'https://www.musictech.net/feed/', type: 'rss', verticals: ['music_production'], dimensions: [1, 3, 5], scrape_interval: 24 },
  { name: 'Sound on Sound', url: 'https://www.soundonsound.com/feed', type: 'rss', verticals: ['music_production'], dimensions: [1, 2, 5], scrape_interval: 24 },
  { name: 'Mix Magazine', url: 'https://www.mixonline.com/feed', type: 'rss', verticals: ['music_production'], dimensions: [1, 3, 5], scrape_interval: 24 },
  { name: 'Tape Op', url: 'https://tapeop.com/feed/', type: 'rss', verticals: ['music_production'], dimensions: [4, 7, 9], scrape_interval: 72 },
  { name: 'Water & Music (Cherie Hu)', url: 'https://www.waterandmusic.com/feed/', type: 'rss', verticals: ['music_production'], dimensions: [1, 3, 6], scrape_interval: 168, notes: 'Best music tech analysis. Verify Substack RSS' },
  { name: 'MIDiA Research', url: 'https://www.midiaresearch.com/feed/', type: 'rss', verticals: ['music_production'], dimensions: [3, 5, 6, 7], scrape_interval: 48 },
  { name: 'Suno Blog', url: 'https://suno.com/blog/rss.xml', type: 'rss', verticals: ['music_production'], dimensions: [1, 5], scrape_interval: 24 },
  { name: 'Udio Blog', url: 'https://www.udio.com/blog/rss.xml', type: 'rss', verticals: ['music_production'], dimensions: [1, 5], scrape_interval: 24 },
  { name: 'r/audioengineering', url: 'https://www.reddit.com/r/audioengineering/.rss', type: 'rss', verticals: ['music_production'], dimensions: [1, 4, 8], scrape_interval: 12 },
  { name: 'r/WeAreTheMusicMakers', url: 'https://www.reddit.com/r/WeAreTheMusicMakers/.rss', type: 'rss', verticals: ['music_production'], dimensions: [1, 3, 9], scrape_interval: 12 },
  { name: 'r/Suno', url: 'https://www.reddit.com/r/Suno/.rss', type: 'rss', verticals: ['music_production', 'digital_humans'], dimensions: [1, 3, 6], scrape_interval: 12 },
  { name: 'Demucs (stem separation)', url: 'https://github.com/facebookresearch/demucs/releases.atom', type: 'rss', verticals: ['music_production'], dimensions: [1, 5], scrape_interval: 72 },
  { name: 'Spleeter', url: 'https://github.com/deezer/spleeter/releases.atom', type: 'rss', verticals: ['music_production'], dimensions: [1, 5], scrape_interval: 72 },
  { name: 'arXiv cs.SD (Sound/Music)', url: 'https://arxiv.org/rss/cs.SD', type: 'rss', verticals: ['music_production'], dimensions: [1, 5], scrape_interval: 24 },
  { name: 'STVDIO Substack', url: 'https://stvdio.substack.com/feed', type: 'rss', verticals: ['music_production'], dimensions: [3, 6], scrape_interval: 168, notes: 'Suno/Udio + copyright + business model analysis' },
  { name: 'Ableton Engineering Blog', url: 'https://www.ableton.com/en/blog/feed/', type: 'rss', verticals: ['music_production'], dimensions: [1, 8], scrape_interval: 168, notes: 'DAW-side ML/stem separation/generative MIDI integration' },
  { name: 'r/edmproduction', url: 'https://www.reddit.com/r/edmproduction/.rss', type: 'rss', verticals: ['music_production'], dimensions: [1, 4, 8], scrape_interval: 12, notes: 'Synth patching, AI stem splitter integration' },
  { name: 'Awesome-Audio (DolbyIO curated)', url: 'https://github.com/DolbyIO/awesome-audio/commits/master.atom', type: 'rss', verticals: ['music_production'], dimensions: [1, 8], scrape_interval: 168 },
]
