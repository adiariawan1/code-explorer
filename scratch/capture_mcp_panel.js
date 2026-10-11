const puppeteer = require('c:/Users/adi ariawan/Documents/code-flow-explorer/web/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const URL = 'http://localhost:3000/view?data=N4IgZglgNgpiBcIDOBDAtgB1gOgwTxABpwBXAOwGMAXCAezKQQG1QIATBUygfQDcUo7FFRjcIItERBl0cRP0Ftho8TEnFBZUUiooATlQQBGDRC3cYZDvAAsxDPvSN4TEBj0QKcALrEKAqGcmXxB-KFg2bgAjAhcuCm4wihIoZW4qWl0oEBCkWhI9L042GDAAAgUhETEJAAp3TxgASngAHTIyzrKIcoavMoAeMoAGNo6uib0UCCQYMoA1ARIYAFE9PVo9WoByLQBzYQheOb6Ybab2yZgqAo7TkABfQlZreMSBZNTqjKypGTQ5KEPik0j8BFJNNpdAYEAAOUzmSzWIwAZnsjjQQRAqkxUjYMwo+TIhhCYUCzDelSU1RxOT8ARgkRiFLA5ASFAAFjAKABrfIk4h5ApFRAlcpJEHfTICWo4pCEMr4pCE8hUFqXLpgqBlAC8Iw1nTAmzKp26HTlYwmEy1ZQA1HqqWkcfUPF4LuNOja9TaAFRlWpGMoAWkVBKJaoNZT011uZS1j2e2NerJ4nO5fJIhmI-0Bad5-IhZih+kM8CMADYEaIkcZ4W4MVi5XSgeEsSn2cCvqJ46SGUzYq529w0NMyM2hYVAWKynmM1RZRIkOqPWV0OHdTPO6DpVAF2p5SNsEZ3VcbnoOmBtgAVHfwMrANeqh7bBMvThD8gkWaRLlQDAwPQ-lkThP2-bhf3-QCq24HQSwQAAmEwQEhCwrAQ+D0SmXEXF7VtmFwiJogHXJ8knYpSjKUDGXAmA-wA2pl1PWNdhgY49E3cJGRfJ430QIcRzMICAU4ASx2g2CYXgeCAFZoJrKTK3rLCggIts2USLl80zZsyWo5kcMFUiRRAadRIYy0ugaYlalnflaiYIxhgVeCnLKFFhm8JomkeEJ+A8FAolgIJeJAPz0h3d4oE+bdfmzYDEHjQVCX-d91IlLtwti5Ci24EoKFSaNrAATmIL8UD2GBguyrQEBKkAUGoOgx1FbkCsZKRCWJGAAA9SxAL0Rlfaq5CMJCGpoegRNofFIHavx6BEXrOBte0KgEKoVDqU5vJ44bjAw+rGsmxA0GmnoIDm0IFp6vqBt9f1AxDJUVWJHbE0hfbiHGpqQO-DrrqWhKdw3e6A2DUNlXDN7QA+ss0UOibmpAaMzy0Dh5q6wHkZjc84x3HzdvYTgwtOSLoqlLKc04e4ktoFK+LSrcKfBaC8ra5EnJAMqKqq2HHK+o6kbZ-RLs6xa+qNdjTTMbpF0QXa+bGwXftFgHbuB1bHRpLbXWaAnEyJ+R9G4R9iQ09MCzi4TEFNrNkGSwEh1s7TWdakXkQAdlK1AeeYGGi2ML2EZ+lr8vd-7Mb622N3SmKZTlBVhiPaG9rLOtvuO7HUdVyPOBR2NLxvLI7wfU6n247wHhCRlfZcUAwA2SQGdTJnu3x4gMlSngtc2tQpCoPB6Zbcldob2gm7eZ27c75uOyiyU26ygeh7JRhR8bruElE-vaE382tOnwfcwCNfEzHiewq1MmF8yln+t32fr4yxL+qPlXIkE9fx+J43Sdj5nsgdwfpPVut9AGvyHl+ain8z4byNnoE2ZczZTx3nvFBHc36ICgR-McVcO5TBFPXNkiN0gEPaogf+i875mAwJmbg2CECsEXMwfmLlCDuRCM9cMCAk5GCeMgEQGAqo6BgBgYwVZarEFYpYPqH1iB+QgAFIKjDsTMJcKwpyHDiBcNVDwo8-CoC0DpjUAChxjpkBSFAXaIixFSQkWWTm0jiScDkaFfQijAqVRUU2dRTk2FaJMmGXR8BeFAN+CEgxRiMAmKmIjYw1jBEIHhorKRxxnGIFcQopRXj4BMP3CwvxmiPLaKCek0J99wmc3uA4yJxjVCxJDnwxMNiEB2FTvzEATjZEB3ke47Jzg8nYQcoU9hxTAmQ2CeU+MDj7C62MMMWp0T6lmOavBBJoiECyXaUhLpLieluP8p4gZqj8m+MIP4sZOiylHjCeCGZbg5lSQWRoKJMSVkIXWbYxSfNHFpO6TVXphzlG5JOUMjRozOGlNLFM-G8B3KzMaAhZ5yFXnLLiXCz5CAg4pM6X8vZAKDkeOBYMoI4KAlXOhTcipdz4UPMRXC5Fhi6kiAacdFEmL4B1h+akmR+K4CAqJTkklBTzlFMhRM65SFpnliqY89yiy3nopsByuqfMDq7IyfsrJRzvFqOGaKiFJSJWUqlbCmVCKRTypecy0x6KLHhA5R0vm8MNV7QFf03Vpz9UXPFS9E1tzsjwGkm06pVqUU2tZc1e1ViQiQBkFAGCugRCerBSM8lUK9GmvCcGi1cgw0AQ2IBeA0b8FsmUNYMAAhZgPAeEAA';
const OUT_DIR = 'C:\\Users\\adi ariawan\\.gemini\\antigravity\\brain\\ce5e61ed-e0aa-4649-a994-cddfe015a6ec';

async function main() {
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1400,1200'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 1200 });

  await page.goto(URL, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 800));

  await page.evaluate(() => {
    localStorage.setItem('cfe_mode', 'bob');
    localStorage.setItem('cfe_mcp_project_name', 'starter_project');
    localStorage.setItem('cfe_mcp_url', 'http://localhost:7860');
    localStorage.setItem('cfe_mcp_project_id', '6780477b-03c0-46de-a1ba-ceb3b82c5b8c');
    localStorage.setItem('cfe_mcp_api_key', 'sk-test');
    localStorage.setItem('cfe_mcp_os', 'windows');
  });

  await page.reload({ waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 800));

  const buttons = await page.$$('button');
  for (const b of buttons) {
    const text = await page.evaluate(el => el.innerText, b);
    if (text.includes('Pengaturan AI')) {
      await b.click();
      break;
    }
  }

  await new Promise(r => setTimeout(r, 800));

  // Find the modal dialog element
  const modalEl = await page.$('.relative.w-full.max-w-lg');
  const screenshotPath = path.join(OUT_DIR, 'mcp_config_panel.png');

  if (modalEl) {
    await modalEl.screenshot({ path: screenshotPath });
  } else {
    await page.screenshot({ path: screenshotPath });
  }

  console.log('Saved screenshot of modal element to:', screenshotPath);
  await browser.close();
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
