extends RefCounted
## 060専用。一時checkoutだけから呼ぶ時刻・回数採取。値を加工しない。
static var spans: Array = []
static var stack: Array[int] = []
static var sequence: int = 0

static func begin(label: String) -> int:
	var index := spans.size()
	spans.append({"label":label,"parent":stack.back() if not stack.is_empty() else -1,"start_us":Time.get_ticks_usec(),"end_us":0})
	stack.append(index)
	return index

static func finish(index: int) -> void:
	spans[index].end_us=Time.get_ticks_usec()
	assert(stack.pop_back()==index)
	if stack.is_empty():
		# 出力時間は根spanの外側。on/offのprocess wallには含まれる。
		print("COST060 ",JSON.stringify({"pid":OS.get_process_id(),"sequence":sequence,"spans":spans}))
		sequence+=1
		spans=[]

static func parse(parser: JSON, text: String, label: String) -> int:
	var tick := begin(label)
	var result := parser.parse(text)
	finish(tick)
	return result

static func decompress(bytes: PackedByteArray, size: int, mode: int, label: String) -> PackedByteArray:
	var tick := begin(label)
	var result := bytes.decompress(size,mode)
	finish(tick)
	return result

static func copy_dictionary(value: Dictionary, deep: bool, label: String) -> Dictionary:
	var tick := begin(label)
	var result := value.duplicate(deep)
	finish(tick)
	return result

static func copy_array(value: Array, deep: bool, label: String) -> Array:
	var tick := begin(label)
	var result := value.duplicate(deep)
	finish(tick)
	return result
