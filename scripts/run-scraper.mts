import { runScraper } from '../lib/scraper/orchestrator.js';

async function main() {
  console.log('🚀 Starting scraper...\n');
  const report = await runScraper();
  
  console.log('📊 Scrape Report:');
  console.log(`  Sources total: ${report.sources_total}`);
  console.log(`  Sources OK: ${report.sources_ok}`);
  console.log(`  Sources errors: ${report.sources_error}`);
  console.log(`  Signals found: ${report.signals_found}`);
  console.log(`  Signals new: ${report.signals_new}`);
  console.log(`  Signals classified: ${report.signals_classified}`);
  console.log(`  Signals inserted: ${report.signals_inserted}`);
  console.log(`  Duration: ${report.duration_ms}ms\n`);
  
  if (report.per_source.length > 0) {
    console.log('📡 Per-source results (first 15):');
    for (const src of report.per_source.slice(0, 15)) {
      const status = src.status === 'ok' ? '✓' : '✗';
      const signals = src.signals_new > 0 ? ` [+${src.signals_new} new]` : '';
      console.log(`  ${status} ${src.source_name.padEnd(30)} ${src.signals_found} found${signals}`);
    }
    if (report.per_source.length > 15) {
      console.log(`  ... and ${report.per_source.length - 15} more sources\n`);
    }
  }
  
  console.log(`✅ Scrape complete. ${report.signals_inserted} signals inserted into database.`);
}

main().catch(err => {
  console.error('❌ Scraper failed:', err);
  process.exit(1);
});
