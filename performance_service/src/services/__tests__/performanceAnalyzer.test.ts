/// <reference types="bun-types" />

import axios from 'axios'
import type { Mock } from 'bun:test'
import { beforeEach, describe, expect, it, jest, mock } from 'bun:test'
import { runLighthouse } from '../../utils/lighthouse'
import { PerformanceAnalyzer } from '../performanceAnalyzer'

// Mock dependencies
mock.module('axios', () => ({
	get: () => ({}),
	head: () => ({}),
}))
mock.module('../../utils/lighthouse', () => ({
	runLighthouse: () => ({}),
}))
mock.module('cheerio', () => ({
	load: () => ({
		$: () => ({
			length: 10,
		}),
	}),
}))

const mockedAxios = axios as unknown as {
	get: Mock<any>
	head: Mock<any>
}
const mockedRunLighthouse = runLighthouse as unknown as Mock<any>

describe('PerformanceAnalyzer', () => {
	const testUrl = 'https://example.com'
	let analyzer: PerformanceAnalyzer

	beforeEach(() => {
		analyzer = new PerformanceAnalyzer(testUrl)
		jest.clearAllMocks()
	})

	describe('analyze', () => {
		beforeEach(() => {
			// Mock successful response
			mockedAxios.get.mockResolvedValue({
				data: '<html><body><script></script><img src="test.jpg"/></body></html>',
				headers: {
					'cache-control': 'max-age=3600',
				},
			})

			mockedAxios.head.mockResolvedValue({})

			mockedRunLighthouse.mockResolvedValue({
				cumulativeLayoutShift: 0.05,
				largestContentfulPaint: 2.0,
				firstInputDelay: 50,
				pageLoadTime: 2000,
			})
		})

		it('should return performance data and recommendations for good performance', async () => {
			const result = await analyzer.analyze()

			expect(result).toHaveProperty('performanceData')
			expect(result).toHaveProperty('recommendations')
			expect(result.recommendations).toHaveLength(0) // No recommendations for good performance
			expect(mockedAxios.get).toHaveBeenCalledWith(testUrl, { timeout: 10000 })
		})

		it('should generate recommendations for poor performance metrics', async () => {
			// Mock poor performance values
			mockedRunLighthouse.mockResolvedValue({
				cumulativeLayoutShift: 0.2, // Bad CLS
				largestContentfulPaint: 3.0, // Bad LCP
				firstInputDelay: 150, // Bad FID
				pageLoadTime: 4000, // Bad Speed Index
			})

			const result = await analyzer.analyze()

			expect(result.recommendations).toHaveLength(4) // Should have recommendations for CLS, LCP, FID, and Speed Index
			expect(result.recommendations[0].category).toBe('PERFORMANCE')
		})

		it('should handle errors during analysis', async () => {
			mockedAxios.get.mockRejectedValue(new Error('Network error'))

			const result = await analyzer.analyze()

			expect(result).toHaveProperty('performanceData')
			expect(result).toHaveProperty('recommendations')
			expect(result.recommendations[0].message).toContain('An error occurred')
		})

		it('should check cache headers', async () => {
			mockedAxios.get.mockResolvedValue({
				data: '<html></html>',
				headers: {
					// Missing cache-control header
				},
			})

			const result = await analyzer.analyze()

			expect(result.recommendations).toContain(
				expect.objectContaining({
					message: expect.stringContaining('Cache-Control headers are missing'),
					category: 'PERFORMANCE',
				})
			)
		})

		it('should handle high HTTP request count', async () => {
			// Mock HTML with many resources
			mockedAxios.get.mockResolvedValue({
				data: '<html>' + '<script></script>'.repeat(51) + '</html>',
				headers: {},
			})

			const result = await analyzer.analyze()

			expect(result.recommendations).toContain(
				expect.objectContaining({
					message: expect.stringContaining('HTTP requests exceeds 50'),
					category: 'PERFORMANCE',
				})
			)
		})
	})
})
