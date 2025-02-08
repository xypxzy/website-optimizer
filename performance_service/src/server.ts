import * as grpc from '@grpc/grpc-js'
import * as protoLoader from '@grpc/proto-loader'
import path from 'path'
import { PerformanceAnalyzer } from './services/performanceAnalyzer'

const PROTO_PATH = path.resolve(__dirname, './protos/performance_service.proto')
const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
	keepCase: true,
	longs: String,
	enums: String,
	defaults: true,
	oneofs: true,
})
const proto = grpc.loadPackageDefinition(packageDefinition) as any

const server = new grpc.Server()

server.addService(proto.performance.PerformanceAnalyzer.service, {
	Analyze: async (
		call: grpc.ServerUnaryCall<any, any>,
		callback: grpc.sendUnaryData<any>
	) => {
		const url = call.request.url
		const performanceAnalyzer = new PerformanceAnalyzer(url)
		const result = await performanceAnalyzer.analyze()

		callback(null, result)
	},
})

const PORT = process.env.PORT || 50053
server.bindAsync(
	'0.0.0.0:50051',
	grpc.ServerCredentials.createInsecure(),
	(err, port) => {
		if (err) throw err
		console.log(`🚀 Performance analyzer listening on port ${port}`)
	}
)
