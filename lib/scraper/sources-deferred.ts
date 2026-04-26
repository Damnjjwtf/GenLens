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
]
