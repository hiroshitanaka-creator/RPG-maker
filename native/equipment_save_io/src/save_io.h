#pragma once
#include <godot_cpp/classes/ref_counted.hpp>
#include <godot_cpp/variant/dictionary.hpp>
#include <godot_cpp/variant/packed_byte_array.hpp>
#include <map>
#include <string>
#include <vector>
#ifdef _WIN32
#include <windows.h>
using NativeHandle = HANDLE;
inline const NativeHandle BAD_HANDLE = INVALID_HANDLE_VALUE;
#else
using NativeHandle = int;
constexpr NativeHandle BAD_HANDLE = -1;
#endif
namespace godot {
class EquipmentSaveIO : public RefCounted {
    GDCLASS(EquipmentSaveIO, RefCounted)
    struct Identity { uint64_t volume=0, file=0, links=0, size=0; bool directory=false; };
    struct OpenFile { NativeHandle handle=BAD_HANDLE; std::string path; Identity identity; bool writing=false; };
    NativeHandle root_handle=BAD_HANDLE;
    std::string root;
    bool ready=false;
    Identity root_identity;
    std::map<int64_t,OpenFile> files;
    std::map<std::string,NativeHandle> locks;
    std::map<std::string,Identity> observations;
    std::vector<NativeHandle> pins;
    int64_t next_id=1;
    int last_error=0;
    bool relative(const String &path,std::string &rel) const;
    NativeHandle parent(const std::string &rel,std::string &leaf,bool create=false);
    NativeHandle open_file(const std::string &rel,bool writing,bool replace=false);
    bool identity(NativeHandle handle,Identity &out);
    bool same(const Identity &a,const Identity &b) const;
    bool locked_path(const std::string &rel) const;
    void close_native(NativeHandle h);
    Dictionary result(bool ok,const char *code="ok");
protected:
    static void _bind_methods();
public:
    ~EquipmentSaveIO();
    bool configure(const String &path);
    bool path_ok(const String &path);
    String relative_path(const String &path);
    bool make_directories(const String &path);
    Dictionary inspect_identity(const String &path);
    Dictionary open_read(const String &path);
    Dictionary read_all(int64_t id);
    Dictionary open_write(const String &path,bool replace);
    Dictionary write_exact(int64_t id,const PackedByteArray &bytes);
    Dictionary flush(int64_t id);
    Dictionary close_file(int64_t id);
    Dictionary rename_file(const String &from,const String &to,bool receipt_replace);
    Dictionary acquire_lock(const String &tx);
    String legacy_link(const String &path);
    int64_t process_state(int64_t pid);
};
}
