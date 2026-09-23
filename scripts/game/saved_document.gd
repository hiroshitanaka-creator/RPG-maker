class_name SavedDocument
extends RefCounted
## ゲーム状態の形式とは別の保存用包み。小さい保存と旧JSONはそのまま扱う。
const THRESHOLD:=262144
const MAX_DECODED:=33554432
const FORMAT:="gzip-json-v1"
static func encode(document: Dictionary)->String:
	var text:=JSON.stringify(document,"",true,true)
	var raw:=text.to_utf8_buffer()
	if raw.size()<THRESHOLD or raw.size()>MAX_DECODED:return text
	var compressed:=raw.compress(FileAccess.COMPRESSION_GZIP)
	var payload:=Marshalls.raw_to_base64(compressed)
	var envelope:={"_storage_format":FORMAT,"decoded_bytes":raw.size(),"sha256":text.sha256_text(),"payload_sha256":payload.sha256_text(),"payload":payload}
	var packed:=JSON.stringify(envelope,"",true,true)
	return packed if packed.to_utf8_buffer().size()<raw.size() else text
static func decode(document: Dictionary)->Dictionary:
	if not document.has("_storage_format"):return document
	if document.get("_storage_format")!=FORMAT or document.size()!=5 or not document.has_all(["decoded_bytes","sha256","payload_sha256","payload"]):return {}
	var length: Variant=document["decoded_bytes"]
	if not (length is int or length is float) or length!=int(length) or length<1 or length>MAX_DECODED:return {}
	for key in ["sha256","payload_sha256","payload"]:
		if not document[key] is String:return {}
	var payload: String=document["payload"]
	if payload.length()>MAX_DECODED*2 or payload.length()%4!=0 or payload.sha256_text()!=document["payload_sha256"]:return {}
	var alphabet:=RegEx.new();alphabet.compile("^[A-Za-z0-9+/]*={0,2}$")
	if alphabet.search(payload)==null:return {}
	var compressed:=Marshalls.base64_to_raw(payload)
	if compressed.size()<18 or compressed[0]!=31 or compressed[1]!=139 or compressed[2]!=8 or compressed.decode_u32(compressed.size()-4)!=int(length):return {}
	var raw:=compressed.decompress(int(length),FileAccess.COMPRESSION_GZIP)
	if raw.size()!=int(length):return {}
	var text:=raw.get_string_from_utf8()
	if text.sha256_text()!=document["sha256"]:return {}
	var parser:=JSON.new()
	if parser.parse(text)!=OK or not parser.data is Dictionary or parser.data.has("_storage_format"):return {}
	return parser.data
