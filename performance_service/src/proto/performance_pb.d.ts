// package: performance
// file: performance.proto

import * as jspb from "google-protobuf";

export class PerformanceData extends jspb.Message {
  getPageLoadTime(): number;
  setPageLoadTime(value: number): void;

  getLargestContentfulPaint(): number;
  setLargestContentfulPaint(value: number): void;

  getCumulativeLayoutShift(): number;
  setCumulativeLayoutShift(value: number): void;

  getFirstInputDelay(): number;
  setFirstInputDelay(value: number): void;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): PerformanceData.AsObject;
  static toObject(includeInstance: boolean, msg: PerformanceData): PerformanceData.AsObject;
  static extensions: {[key: number]: jspb.ExtensionFieldInfo<jspb.Message>};
  static extensionsBinary: {[key: number]: jspb.ExtensionFieldBinaryInfo<jspb.Message>};
  static serializeBinaryToWriter(message: PerformanceData, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): PerformanceData;
  static deserializeBinaryFromReader(message: PerformanceData, reader: jspb.BinaryReader): PerformanceData;
}

export namespace PerformanceData {
  export type AsObject = {
    pageLoadTime: number,
    largestContentfulPaint: number,
    cumulativeLayoutShift: number,
    firstInputDelay: number,
  }
}

export class PerformanceRequest extends jspb.Message {
  getUrl(): string;
  setUrl(value: string): void;

  getCorrelationId(): string;
  setCorrelationId(value: string): void;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): PerformanceRequest.AsObject;
  static toObject(includeInstance: boolean, msg: PerformanceRequest): PerformanceRequest.AsObject;
  static extensions: {[key: number]: jspb.ExtensionFieldInfo<jspb.Message>};
  static extensionsBinary: {[key: number]: jspb.ExtensionFieldBinaryInfo<jspb.Message>};
  static serializeBinaryToWriter(message: PerformanceRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): PerformanceRequest;
  static deserializeBinaryFromReader(message: PerformanceRequest, reader: jspb.BinaryReader): PerformanceRequest;
}

export namespace PerformanceRequest {
  export type AsObject = {
    url: string,
    correlationId: string,
  }
}

