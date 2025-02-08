import lighthouse from 'lighthouse'
import puppeteer from 'puppeteer'
import { URL } from 'url'
import path from 'path'

export async function runLighthouse(url: string) {
	const browser = await puppeteer.launch({
		executablePath: process.env.LIGHTHOUSE_CHROMIUM_PATH || '/usr/bin/chromium',
		args: [
			'--no-sandbox',
			'--disable-setuid-sandbox',
			'--disable-dev-shm-usage',
			'--disable-gpu',
		],
	})

	try {
		const result = await lighthouse(url, {
			port: Number(new URL(browser.wsEndpoint()).port),
			output: 'json',
			logLevel: 'error',
			onlyCategories: ['performance'],
			locale: 'en',
		})

		if (!result) {
			throw new Error('Lighthouse run failed')
		}

		const { lhr } = result

		return {
			pageLoadTime: lhr.audits['speed-index'].numericValue ?? 0,
			largestContentfulPaint:
				lhr.audits['largest-contentful-paint'].numericValue ?? 0,
			cumulativeLayoutShift:
				lhr.audits['cumulative-layout-shift'].numericValue ?? 0,
			firstInputDelay: lhr.audits['max-potential-fid'].numericValue ?? 0,
		}
	} finally {
		await browser.close()
	}
}
