# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: analyzer.proto
# Protobuf Python Version: 5.28.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    28,
    1,
    '',
    'analyzer.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0e\x61nalyzer.proto\x12\x08\x61nalyzer\"!\n\x0e\x41nalyzeRequest\x12\x0f\n\x07\x63ontent\x18\x01 \x01(\t\"\xc9\x01\n\x0f\x41nalyzeResponse\x12T\n\x16\x66requency_distribution\x18\x01 \x03(\x0b\x32\x34.analyzer.AnalyzeResponse.FrequencyDistributionEntry\x12\"\n\x08\x65ntities\x18\x02 \x03(\x0b\x32\x10.analyzer.Entity\x1a<\n\x1a\x46requencyDistributionEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\x05:\x02\x38\x01\"%\n\x06\x45ntity\x12\x0c\n\x04type\x18\x01 \x01(\t\x12\r\n\x05names\x18\x02 \x03(\t2Q\n\x0f\x41nalyzerService\x12>\n\x07\x41nalyze\x12\x18.analyzer.AnalyzeRequest\x1a\x19.analyzer.AnalyzeResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'analyzer_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_ANALYZERESPONSE_FREQUENCYDISTRIBUTIONENTRY']._loaded_options = None
  _globals['_ANALYZERESPONSE_FREQUENCYDISTRIBUTIONENTRY']._serialized_options = b'8\001'
  _globals['_ANALYZEREQUEST']._serialized_start=28
  _globals['_ANALYZEREQUEST']._serialized_end=61
  _globals['_ANALYZERESPONSE']._serialized_start=64
  _globals['_ANALYZERESPONSE']._serialized_end=265
  _globals['_ANALYZERESPONSE_FREQUENCYDISTRIBUTIONENTRY']._serialized_start=205
  _globals['_ANALYZERESPONSE_FREQUENCYDISTRIBUTIONENTRY']._serialized_end=265
  _globals['_ENTITY']._serialized_start=267
  _globals['_ENTITY']._serialized_end=304
  _globals['_ANALYZERSERVICE']._serialized_start=306
  _globals['_ANALYZERSERVICE']._serialized_end=387
# @@protoc_insertion_point(module_scope)
