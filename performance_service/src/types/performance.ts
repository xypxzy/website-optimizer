export interface IPerformanceData {
	pageLoadTime: number
	timeToFirstByte: number
	httpRequestCount: number
	cumulativeLayoutShift: number
	largestContentfulPaint: number
}

export interface IRecommendation {
	message: string
	severity?: 'low' | 'medium' | 'high'
	category: 'PERFORMANCE'
}
