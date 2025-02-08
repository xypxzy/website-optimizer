import axios from 'axios'
import * as cheerio from 'cheerio'
import type { IPerformanceData, IRecommendation } from '../types/performance'
import { runLighthouse } from '../utils/lighthouse'

export class PerformanceAnalyzer {
	private url: string
	private performanceData: Partial<IPerformanceData> = {}
	private recommendations: IRecommendation[] = []

	constructor(url: string) {
		this.url = url
	}

	async analyze() {
		try {
			const startTime = Date.now()
			const response = await axios.get(this.url, { timeout: 10000 })
			const endTime = Date.now()

			// Page Load Time
			this.performanceData.pageLoadTime = (endTime - startTime) / 1000
			this.checkPageLoadTime()

			// Time to First Byte
			this.performanceData.timeToFirstByte = await this.getTTFB()
			this.checkTTFB()

			// HTTP Request Count
			this.performanceData.httpRequestCount = this.getHttpRequestCount(
				response.data
			)
			this.checkHttpRequestCount()

			// Cache Headers
			this.checkCacheHeaders(response.headers)

			// Lighthouse Analysis
			const lighthouseData = await runLighthouse(this.url)
			this.performanceData.cumulativeLayoutShift =
				lighthouseData.cumulativeLayoutShift
			this.performanceData.largestContentfulPaint =
				lighthouseData.largestContentfulPaint

			this.checkCLS(lighthouseData.cumulativeLayoutShift || 0)
			this.checkLCP(lighthouseData.largestContentfulPaint || 0)
			this.checkFID(lighthouseData.firstInputDelay || 0)
			this.checkSpeedIndex(lighthouseData.pageLoadTime || 0)

			return {
				performanceData: this.performanceData,
				recommendations: this.recommendations,
			}
		} catch (error) {
			console.error('Performance analysis error:', error)
			this.recommendations.push({
				message: 'An error occurred during performance analysis.',
				category: 'PERFORMANCE',
			})

			return {
				performanceData: this.performanceData,
				recommendations: this.recommendations,
			}
		}
	}

	private async getTTFB(): Promise<number> {
		try {
			const start = Date.now()
			await axios.head(this.url, { timeout: 5000 })
			const end = Date.now()
			return (end - start) / 1000
		} catch (error) {
			console.error('TTFB calculation failed:', error)
			return -1
		}
	}

	private getHttpRequestCount(html: string): number {
		try {
			const $ = cheerio.load(html)
			const resourceTags = $('script, link, img')
			return resourceTags.length
		} catch (error) {
			console.error('HTTP request count failed:', error)
			return 0
		}
	}

	private checkPageLoadTime() {
		if ((this.performanceData.pageLoadTime || 0) > 3.0) {
			this.recommendations.push({
				message:
					'Page load time exceeds 3 seconds. Optimize resources and server response time.',
				category: 'PERFORMANCE',
			})
		}
	}

	private checkTTFB() {
		if ((this.performanceData.timeToFirstByte || 0) > 0.2) {
			this.recommendations.push({
				message:
					'Time To First Byte (TTFB) exceeds 200ms. Optimize server response time.',
				category: 'PERFORMANCE',
			})
		}
	}

	private checkHttpRequestCount() {
		if ((this.performanceData.httpRequestCount || 0) > 50) {
			this.recommendations.push({
				message:
					'The number of HTTP requests exceeds 50. Consider combining resources to reduce requests.',
				category: 'PERFORMANCE',
			})
		}
	}

	private checkCacheHeaders(headers: any) {
		const cacheControl = headers['cache-control'] || ''
		if (!cacheControl.includes('max-age')) {
			this.recommendations.push({
				message:
					'Cache-Control headers are missing or not optimized. Set max-age for static resources.',
				category: 'PERFORMANCE',
			})
		}
	}

	private checkCLS(cls: number) {
		if (cls > 0.1) {
			this.recommendations.push({
				message: `Cumulative Layout Shift (CLS) is ${cls.toFixed(
					2
				)}, which exceeds the recommended threshold of 0.1. Optimize layout stability.`,
				category: 'PERFORMANCE',
			})
		}
	}

	private checkLCP(lcp: number) {
		if (lcp > 2.5) {
			this.recommendations.push({
				message: `Largest Contentful Paint (LCP) is ${lcp.toFixed(
					2
				)} seconds, which exceeds the recommended threshold of 2.5 seconds.`,
				category: 'PERFORMANCE',
			})
		}
	}

	private checkFID(fid: number) {
		if (fid > 100) {
			this.recommendations.push({
				message: `First Input Delay (FID) is ${fid}ms, which exceeds the recommended threshold of 100ms.`,
				category: 'PERFORMANCE',
			})
		}
	}

	private checkSpeedIndex(speedIndex: number) {
		if (speedIndex > 3000) {
			this.recommendations.push({
				message: `Speed Index is ${speedIndex}, which exceeds the recommended threshold of 3000.`,
				category: 'PERFORMANCE',
			})
		}
	}
}
