import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1180, height: 1400 }, colorScheme: 'light' });
await p.goto('file:///home/user/SKtommy/report/index.html', { waitUntil: 'networkidle' });
await p.waitForTimeout(1200);
await p.emulateMedia({ media: 'print', colorScheme: 'light' });
await p.waitForTimeout(400);
await p.pdf({
  path: '/home/user/SKtommy/report/nomura-em-holdings-2007-2025.pdf',
  format: 'A4', printBackground: true,
  margin: { top: '16mm', bottom: '18mm', left: '14mm', right: '14mm' },
  displayHeaderFooter: true,
  headerTemplate: '<div></div>',
  footerTemplate: '<div style="width:100%;font-family:Arial,sans-serif;font-size:7pt;color:#8b9099;padding:0 14mm;display:flex;justify-content:space-between"><span>Nomura (ex-Delaware) Emerging Markets Fund · SEC CIK 875610 · FY2007–FY2025</span><span class="pageNumber"></span></div>'
});
await b.close();
console.log('done');
