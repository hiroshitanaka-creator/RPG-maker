#include "save_io.h"
#include <godot_cpp/core/class_db.hpp>
#include <godot_cpp/godot.hpp>
#include <algorithm>
#include <cstring>
#include <cerrno>
#include <limits>
#ifdef _WIN32
#include <cwctype>
#include <winternl.h>
#else
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/file.h>
#include <sys/syscall.h>
#include <signal.h>
#include <unistd.h>
#include <linux/fs.h>
#endif
using namespace godot;
namespace {
std::string utf8(const String &s) { return std::string(s.utf8().get_data()); }
#ifdef _WIN32
std::wstring wide(const std::string &s) {
    int count=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s.c_str(),-1,nullptr,0);
    if(count<=0)return {};
    std::wstring value(count,L'\0');
    MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s.c_str(),-1,value.data(),count);
    value.resize(count-1);return value;
}
std::wstring os_path(const std::string &s) {
    auto value=wide(s);std::replace(value.begin(),value.end(),L'/',L'\\');
    return L"\\\\?\\"+value;
}
int os_error() {return static_cast<int>(GetLastError());}
bool absent(int error) {return error==ERROR_FILE_NOT_FOUND || error==ERROR_PATH_NOT_FOUND;}
// NTのRootDirectoryで名前解決を固定。API欠落時は絶対pathへのfallbackをしない。
using CreateRelative = NTSTATUS (NTAPI *)(PHANDLE,ACCESS_MASK,POBJECT_ATTRIBUTES,PIO_STATUS_BLOCK,PLARGE_INTEGER,ULONG,ULONG,ULONG,ULONG,PVOID,ULONG);
using RenameRelative = NTSTATUS (NTAPI *)(HANDLE,PIO_STATUS_BLOCK,PVOID,ULONG,FILE_INFORMATION_CLASS);
using StatusError = ULONG (NTAPI *)(NTSTATUS);
void nt_error(NTSTATUS status) {
    auto convert=reinterpret_cast<StatusError>(GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"RtlNtStatusToDosError"));
    SetLastError(convert?convert(status):ERROR_NOT_SUPPORTED);
}
HANDLE relative_open(HANDLE parent,const std::string &leaf,ACCESS_MASK access,ULONG share,ULONG disposition,ULONG type=0) {
    auto create=reinterpret_cast<CreateRelative>(GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"NtCreateFile"));
    auto name=wide(leaf);
    if(!create || name.empty() || name.size()>32766){SetLastError(ERROR_NOT_SUPPORTED);return BAD_HANDLE;}
    UNICODE_STRING unicode{};unicode.Buffer=name.data();unicode.Length=USHORT(name.size()*sizeof(wchar_t));unicode.MaximumLength=unicode.Length;
    OBJECT_ATTRIBUTES attributes{};
    InitializeObjectAttributes(&attributes,&unicode,OBJ_CASE_INSENSITIVE|OBJ_DONT_REPARSE,parent,nullptr);
    IO_STATUS_BLOCK io{};HANDLE handle=BAD_HANDLE;
    auto status=create(&handle,access|SYNCHRONIZE,&attributes,&io,nullptr,FILE_ATTRIBUTE_NORMAL,share,disposition,
        type|FILE_SYNCHRONOUS_IO_NONALERT|FILE_OPEN_REPARSE_POINT,nullptr,0);
    if(status<0){nt_error(status);return BAD_HANDLE;}return handle;
}
bool relative_rename(HANDLE source,HANDLE parent,const std::string &leaf,bool replace) {
    auto rename=reinterpret_cast<RenameRelative>(GetProcAddress(GetModuleHandleW(L"ntdll.dll"),"NtSetInformationFile"));
    if(!rename){SetLastError(ERROR_NOT_SUPPORTED);return false;}
    auto name=wide(leaf);std::vector<unsigned char> data(offsetof(FILE_RENAME_INFORMATION,FileName)+name.size()*sizeof(wchar_t));
    auto info=reinterpret_cast<FILE_RENAME_INFORMATION*>(data.data());info->ReplaceIfExists=replace;info->RootDirectory=parent;
    info->FileNameLength=ULONG(name.size()*sizeof(wchar_t));memcpy(info->FileName,name.data(),info->FileNameLength);
    IO_STATUS_BLOCK io{};auto status=rename(source,&io,info,ULONG(data.size()),FileRenameInformation);
    if(status<0){nt_error(status);return false;}return true;
}
#else
int os_error() {return errno;}
bool absent(int error) {return error==ENOENT;}
#endif
bool components(const std::string &s) {
    if(s.find('\0')!=std::string::npos)return false;
    size_t start=0;
    while(start<s.size()) {
        auto end=s.find('/',start);if(end==std::string::npos)end=s.size();
        auto part=s.substr(start,end-start);
        if(part.empty() || part=="." || part=="..")return false;
#ifdef _WIN32
        if(part.back()=='.' || part.back()==' ' || part.find_first_of(":\\<>\"|?*")!=std::string::npos)return false;
        for(unsigned char c:part)if(c<32)return false;
        auto base=part.substr(0,part.find('.'));
        std::transform(base.begin(),base.end(),base.begin(),[](unsigned char c){return std::toupper(c);});
        if(base=="CON" || base=="PRN" || base=="AUX" || base=="NUL" || base=="CONIN$" || base=="CONOUT$")return false;
        if(base.size()==4 && (base.substr(0,3)=="COM" || base.substr(0,3)=="LPT") && base[3]>='1' && base[3]<='9')return false;
        if(base.size()==5 && (base.substr(0,3)=="COM" || base.substr(0,3)=="LPT") &&
            (base.substr(3)=="\xC2\xB9" || base.substr(3)=="\xC2\xB2" || base.substr(3)=="\xC2\xB3"))return false;
#endif
        start=end+1;
    }
    return true;
}
}
bool NativePathLess::operator()(const std::string &a,const std::string &b) const {
#ifdef _WIN32
    auto left=wide(a),right=wide(b);
    return CompareStringOrdinal(left.c_str(),int(left.size()),right.c_str(),int(right.size()),TRUE)==CSTR_LESS_THAN;
#else
    return a<b;
#endif
}
void EquipmentSaveIO::close_native(NativeHandle h) {
    if(h==BAD_HANDLE)return;
#ifdef _WIN32
    CloseHandle(h);
#else
    ::close(h);
#endif
}
EquipmentSaveIO::~EquipmentSaveIO() {
    for(auto &item:files)close_native(item.second.handle);
    for(auto &item:locks)close_native(item.second);
    for(auto pin:pins)close_native(pin);
    close_native(root_handle);
}
Dictionary EquipmentSaveIO::result(bool ok,const char *code) {
    Dictionary out;out["ok"]=ok;out["reason_code"]=String(code);out["os_error"]=last_error;return out;
}
bool EquipmentSaveIO::same(const Identity &a,const Identity &b) const {return a.volume==b.volume && a.file==b.file;}
bool EquipmentSaveIO::identity(NativeHandle h,Identity &out) {
#ifdef _WIN32
    BY_HANDLE_FILE_INFORMATION i{};
    if(!GetFileInformationByHandle(h,&i)){last_error=os_error();return false;}
    if(i.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)return false;
    out.volume=i.dwVolumeSerialNumber;out.file=(uint64_t(i.nFileIndexHigh)<<32)|i.nFileIndexLow;
    out.links=i.nNumberOfLinks;out.size=(uint64_t(i.nFileSizeHigh)<<32)|i.nFileSizeLow;
    out.directory=(i.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)!=0;
#else
    struct stat i{};if(fstat(h,&i)<0){last_error=os_error();return false;}
    if(!S_ISDIR(i.st_mode) && !S_ISREG(i.st_mode))return false;
    out.volume=i.st_dev;out.file=i.st_ino;out.links=i.st_nlink;out.size=i.st_size;out.directory=S_ISDIR(i.st_mode);
#endif
    return true;
}
bool EquipmentSaveIO::configure(const String &path) {
    if(root_handle!=BAD_HANDLE)return false;
    root=utf8(path);std::replace(root.begin(),root.end(),'\\','/');
    while(root.size()>1 && root.back()=='/')root.pop_back();
#ifdef _WIN32
    if(root.size()<4 || root[1]!=':' || root[2]!='/' || !components(root.substr(3)))return false;
    // 全祖先をreparse無しで開き、delete共有を与えずroot差替えを防ぐ。
    auto ancestor=CreateFileW(os_path(root.substr(0,3)).c_str(),FILE_READ_ATTRIBUTES|FILE_LIST_DIRECTORY|SYNCHRONIZE,
        FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_EXISTING,FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
    if(ancestor==BAD_HANDLE)return false;
    pins.push_back(ancestor);
    size_t start=3;
    while(start<root.size()) {
        auto end=root.find('/',start);if(end==std::string::npos)end=root.size();
        auto h=relative_open(ancestor,root.substr(start,end-start),FILE_READ_ATTRIBUTES|FILE_LIST_DIRECTORY,
            FILE_SHARE_READ|FILE_SHARE_WRITE,FILE_OPEN,FILE_DIRECTORY_FILE);
        Identity i;if(h==BAD_HANDLE || !identity(h,i) || !i.directory){close_native(h);return false;}
        pins.push_back(h);ancestor=h;start=end+1;
    }
    root_handle=pins.back();pins.pop_back();
    wchar_t filesystem[64]{};
    if(!GetVolumeInformationByHandleW(root_handle,nullptr,0,nullptr,nullptr,nullptr,filesystem,64) || wcscmp(filesystem,L"NTFS")!=0)return false;
#else
    if(root.size()<2 || root[0]!='/' || !components(root.substr(1)))return false;
    int h=::open("/",O_RDONLY|O_DIRECTORY|O_CLOEXEC);
    size_t start=1;
    while(start<root.size()) {
        auto end=root.find('/',start);if(end==std::string::npos)end=root.size();
        auto part=root.substr(start,end-start);
        int next=openat(h,part.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);close_native(h);
        if(next<0){last_error=os_error();return false;}h=next;start=end+1;
    }
    root_handle=h;
#endif
    if(!identity(root_handle,root_identity))return false;
    ready=true;return true;
}
bool EquipmentSaveIO::relative(const String &path,std::string &rel) const {
    if(!ready)return false;
    auto p=utf8(path);
#ifdef _WIN32
    std::replace(p.begin(),p.end(),'\\','/');
    if(p.size()<root.size())return false;
    auto a=wide(p.substr(0,root.size())),b=wide(root);
    if(CompareStringOrdinal(a.c_str(),int(a.size()),b.c_str(),int(b.size()),TRUE)!=CSTR_EQUAL)return false;
#else
    if(p.compare(0,root.size(),root)!=0)return false;
#endif
    if(p.size()==root.size()){rel="";return true;}
    if(p[root.size()]!='/')return false;
    rel=p.substr(root.size()+1);return components(rel);
}
NativeHandle EquipmentSaveIO::parent(const std::string &rel,std::string &leaf,bool create) {
    auto end=rel.rfind('/');leaf=end==std::string::npos?rel:rel.substr(end+1);
    std::string dirs=end==std::string::npos?"":rel.substr(0,end);
#ifdef _WIN32
    Identity anchor;
    if(!identity(root_handle,anchor) || !same(anchor,root_identity) || !anchor.directory)return BAD_HANDLE;
    for(auto pin:pins){Identity checked;if(!identity(pin,checked) || !checked.directory || checked.volume!=root_identity.volume)return BAD_HANDLE;}
    std::string cursor=root;size_t start=0;NativeHandle current=root_handle;
    while(start<dirs.size()) {
        auto finish=dirs.find('/',start);if(finish==std::string::npos)finish=dirs.size();
        cursor+="/"+dirs.substr(start,finish-start);
        auto held=directory_pins.find(cursor);
        if(held!=directory_pins.end()){
            Identity checked;
            if(!identity(held->second,checked) || !checked.directory || checked.volume!=root_identity.volume)return BAD_HANDLE;
            current=held->second;start=finish+1;continue;
        }
        auto h=relative_open(current,dirs.substr(start,finish-start),FILE_READ_ATTRIBUTES|FILE_LIST_DIRECTORY,
            FILE_SHARE_READ|FILE_SHARE_WRITE,create?FILE_OPEN_IF:FILE_OPEN,FILE_DIRECTORY_FILE);
        Identity i;if(h==BAD_HANDLE || !identity(h,i) || !i.directory || i.volume!=root_identity.volume){last_error=os_error();close_native(h);return BAD_HANDLE;}
        // delete共有を拒否している生存handleなので、名前の差替えはOSが拒否する。
        // file内容・validator結果はcacheしない。
        pins.push_back(h);directory_pins[cursor]=h;current=h;start=finish+1;
    }
    // 呼出しでcloseできる独立handle。
    HANDLE copy=BAD_HANDLE;auto source=current;
    if(!DuplicateHandle(GetCurrentProcess(),source,GetCurrentProcess(),&copy,0,FALSE,DUPLICATE_SAME_ACCESS))last_error=os_error();
    return copy;
#else
    int fd=dup(root_handle);size_t start=0;
    while(start<dirs.size()) {
        auto finish=dirs.find('/',start);if(finish==std::string::npos)finish=dirs.size();
        auto part=dirs.substr(start,finish-start);
        if(create && mkdirat(fd,part.c_str(),0700)<0 && errno!=EEXIST){last_error=os_error();close_native(fd);return BAD_HANDLE;}
        int next=openat(fd,part.c_str(),O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);close_native(fd);
        Identity i;if(next<0 || !identity(next,i) || !i.directory || i.volume!=root_identity.volume){last_error=os_error();close_native(next);return BAD_HANDLE;}
        fd=next;start=finish+1;
    }
    return fd;
#endif
}
NativeHandle EquipmentSaveIO::open_file(const std::string &rel,bool writing,bool replace) {
    std::string leaf;auto p=parent(rel,leaf);if(p==BAD_HANDLE)return BAD_HANDLE;
#ifdef _WIN32
    auto h=relative_open(p,leaf,writing?GENERIC_READ|GENERIC_WRITE:GENERIC_READ,
        writing?FILE_SHARE_READ:(FILE_SHARE_READ|FILE_SHARE_WRITE),writing && !replace?FILE_CREATE:FILE_OPEN,FILE_NON_DIRECTORY_FILE);
#else
    int flags=(writing?O_RDWR:O_RDONLY)|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK;
    if(writing && !replace)flags|=O_CREAT|O_EXCL;
    auto h=openat(p,leaf.c_str(),flags,0600);
#endif
    last_error=h==BAD_HANDLE?os_error():0;close_native(p);
    if(h==BAD_HANDLE)return h;
    Identity i;if(!identity(h,i) || i.directory || i.volume!=root_identity.volume || (writing && i.links!=1)){close_native(h);return BAD_HANDLE;}
    if(writing && replace) {
        auto known=observations.find(rel);
        if(known!=observations.end() && !same(known->second,i)){close_native(h);return BAD_HANDLE;}
#ifdef _WIN32
        LARGE_INTEGER zero{};
        if(!SetFilePointerEx(h,zero,nullptr,FILE_BEGIN) || !SetEndOfFile(h)){last_error=os_error();close_native(h);return BAD_HANDLE;}
#else
        if(ftruncate(h,0)<0){last_error=os_error();close_native(h);return BAD_HANDLE;}
#endif
    }
    auto observed=observations.find(rel);
    if(!writing && observed!=observations.end() && !same(observed->second,i)){close_native(h);return BAD_HANDLE;}
    observations[rel]=i;return h;
}
String EquipmentSaveIO::relative_path(const String &path) {
    std::string rel;return relative(path,rel)?String::utf8(rel.c_str()):String();
}
bool EquipmentSaveIO::path_ok(const String &path) {
    std::string rel;if(!relative(path,rel))return false;
#ifdef _WIN32
    Identity anchor;if(!identity(root_handle,anchor) || !same(anchor,root_identity) || !anchor.directory)return false;
#endif
    if(rel.empty())return true;
    // 未作成末尾も、全ての存在する成分をsymlink無し・同volumeで確認。
#ifndef _WIN32
    int fd=dup(root_handle);size_t start=0;
    while(start<rel.size()) {
        auto end=rel.find('/',start);if(end==std::string::npos)end=rel.size();
        auto part=rel.substr(start,end-start);
        auto next=openat(fd,part.c_str(),O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK|(end<rel.size()?O_DIRECTORY:0));
        int error=next<0?os_error():0;close_native(fd);
        if(next<0){last_error=error;return absent(error);}
        Identity i;bool valid=identity(next,i) && i.volume==root_identity.volume && (end==rel.size() || i.directory);
        if(!valid){close_native(next);return false;}fd=next;start=end+1;
    }
    close_native(fd);return true;
#else
    std::string cursor;size_t start=0;
    while(start<rel.size()) {
        auto end=rel.find('/',start);if(end==std::string::npos)end=rel.size();
        if(!cursor.empty())cursor+='/';cursor+=rel.substr(start,end-start);
        auto held=directory_pins.find(root+"/"+cursor);
        if(held!=directory_pins.end()){
            Identity checked;
            if(!identity(held->second,checked) || !checked.directory || checked.volume!=root_identity.volume)return false;
            start=end+1;continue;
        }
        std::string leaf;auto p=parent(cursor,leaf);if(p==BAD_HANDLE)return false;
        auto h=relative_open(p,leaf,FILE_READ_ATTRIBUTES,FILE_SHARE_READ|FILE_SHARE_WRITE,FILE_OPEN);
        int error=h==BAD_HANDLE?os_error():0;close_native(p);
        if(h==BAD_HANDLE){last_error=error;return absent(error);}
        Identity i;bool valid=identity(h,i) && i.volume==root_identity.volume && (end==rel.size() || i.directory);close_native(h);
        if(!valid)return false;start=end+1;
    }
    return true;
#endif
}
bool EquipmentSaveIO::make_directories(const String &path) {
    std::string rel;if(!relative(path,rel) || rel.empty())return false;
    std::string leaf;auto p=parent(rel+"/sentinel",leaf,true);if(p==BAD_HANDLE)return false;close_native(p);return true;
}
Dictionary EquipmentSaveIO::inspect_identity(const String &path) {
    std::string rel;if(!relative(path,rel) || rel.empty())return result(false,"path_invalid");
    auto h=open_file(rel,false);if(h==BAD_HANDLE)return result(false,"read_failed");
    Identity i;bool ok=identity(h,i);close_native(h);auto r=result(ok);
    r["volume"]=String::num_uint64(i.volume);r["file"]=String::num_uint64(i.file);r["links"]=int64_t(i.links);r["size"]=int64_t(i.size);return r;
}
Dictionary EquipmentSaveIO::open_read(const String &path) {
    std::string rel;if(!relative(path,rel) || !path_ok(path))return result(false,"path_invalid");
    auto h=open_file(rel,false);if(h==BAD_HANDLE)return result(false,"read_failed");
    Identity i;if(!identity(h,i)){close_native(h);return result(false,"read_failed");}
    auto id=next_id++;files[id]={h,rel,i,false};auto r=result(true);r["handle"]=id;r["size"]=int64_t(i.size);return r;
}
Dictionary EquipmentSaveIO::read_all(int64_t id) {
    auto found=files.find(id);if(found==files.end())return result(false,"read_failed");
    auto &f=found->second;Identity i;if(!identity(f.handle,i) || !same(i,f.identity) || i.size>33554432)return result(false,"read_failed");
    PackedByteArray bytes;bytes.resize(i.size);uint64_t offset=0;
    while(offset<i.size) {
#ifdef _WIN32
        DWORD count=0;if(!ReadFile(f.handle,bytes.ptrw()+offset,DWORD(std::min<uint64_t>(i.size-offset,1<<20)),&count,nullptr)){last_error=os_error();return result(false,"read_failed");}
#else
        auto count=::read(f.handle,bytes.ptrw()+offset,i.size-offset);
        if(count<0 && errno==EINTR)continue;
        if(count<0){last_error=os_error();return result(false,"read_failed");}
#endif
        if(!count)return result(false,"read_failed");offset+=count;
    }
    Identity after;if(!identity(f.handle,after) || after.size!=i.size)return result(false,"read_failed");
    auto r=result(true);r["bytes"]=bytes;r["size"]=int64_t(i.size);return r;
}
bool EquipmentSaveIO::locked_path(const std::string &rel) const {
    NativePathLess compare;
    for(auto &item:locks){auto prefix=item.first+"/",actual=rel.substr(0,prefix.size());
        if(!compare(actual,prefix) && !compare(prefix,actual))return true;}
    return false;
}
Dictionary EquipmentSaveIO::open_write(const String &path,bool replace) {
    std::string rel;if(!relative(path,rel) || !path_ok(path))return result(false,"path_invalid");
    if(!locked_path(rel))return result(false,"busy");
    // 再利用可能なのはGDScriptが取引を照合した未完tmpだけ。確定fileは切詰め不可。
    if(replace && (rel.size()<4 || rel.substr(rel.size()-4)!=".tmp"))return result(false,"conflict");
    auto h=open_file(rel,true,false);
    if(h==BAD_HANDLE && replace)h=open_file(rel,true,true);
    if(h==BAD_HANDLE)return result(false,"write_failed");
    Identity i;if(!identity(h,i)){close_native(h);return result(false,"write_failed");}
    auto id=next_id++;files[id]={h,rel,i,true};auto r=result(true);r["handle"]=id;return r;
}
Dictionary EquipmentSaveIO::write_exact(int64_t id,const PackedByteArray &bytes) {
    auto found=files.find(id);if(found==files.end() || !found->second.writing)return result(false,"write_failed");
    auto h=found->second.handle;int64_t offset=0;
    while(offset<bytes.size()) {
#ifdef _WIN32
        DWORD count=0;if(!WriteFile(h,bytes.ptr()+offset,DWORD(std::min<int64_t>(bytes.size()-offset,1<<20)),&count,nullptr)){last_error=os_error();return result(false,"write_failed");}
#else
        auto count=::write(h,bytes.ptr()+offset,bytes.size()-offset);
        if(count<0 && errno==EINTR)continue;
        if(count<0){last_error=os_error();return result(false,"write_failed");}
#endif
        if(!count)return result(false,"write_failed");offset+=count;
    }
    return result(true);
}
Dictionary EquipmentSaveIO::flush(int64_t id) {
    auto found=files.find(id);if(found==files.end())return result(false,"write_failed");
#ifdef _WIN32
    bool ok=FlushFileBuffers(found->second.handle)!=0;
#else
    bool ok=fsync(found->second.handle)==0;
#endif
    last_error=ok?0:os_error();return result(ok,ok?"ok":"write_failed");
}
Dictionary EquipmentSaveIO::close_file(int64_t id) {
    auto found=files.find(id);if(found==files.end())return result(false,"write_failed");
    auto h=found->second.handle;files.erase(found);
#ifdef _WIN32
    bool ok=CloseHandle(h)!=0;
#else
    bool ok=::close(h)==0;
#endif
    last_error=ok?0:os_error();return result(ok,ok?"ok":"write_failed");
}
Dictionary EquipmentSaveIO::rename_file(const String &from,const String &to,bool receipt_replace) {
    std::string a,b;if(!relative(from,a) || !relative(to,b) || !path_ok(from) || !path_ok(to))return result(false,"path_invalid");
    NativePathLess names;if(!names(a,b) && !names(b,a))return result(false,"target_conflict");
    NativePathLess compare;auto source_dir=a.substr(0,a.rfind('/')),target_dir=b.substr(0,b.rfind('/'));
    if(!locked_path(a) || !locked_path(b) || compare(source_dir,target_dir) || compare(target_dir,source_dir))return result(false,"busy");
    if(receipt_replace && (a.substr(a.rfind('/')+1)!="receipt.tmp" || b.substr(b.rfind('/')+1)!="receipt.json"))return result(false,"conflict");
    auto expected=observations.find(a);if(expected==observations.end())return result(false,"rename_failed");
    std::string src,dst;auto p=parent(a,src),q=parent(b,dst);
    if(p==BAD_HANDLE || q==BAD_HANDLE){close_native(p);close_native(q);return result(false,"rename_failed");}
    bool ok=false;
#ifdef _WIN32
    auto h=relative_open(p,src,GENERIC_READ|DELETE,FILE_SHARE_READ,FILE_OPEN,FILE_NON_DIRECTORY_FILE);
    Identity i;if(h!=BAD_HANDLE && identity(h,i) && same(i,expected->second) && i.links==1) {
        // receipt置換先もlink数を確認。delete共有なしの他handleならOSが拒否する。
        bool target_safe=true;
        auto target=relative_open(q,dst,FILE_READ_ATTRIBUTES,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,FILE_OPEN,FILE_NON_DIRECTORY_FILE);
        if(target!=BAD_HANDLE){Identity t;target_safe=identity(target,t) && t.volume==root_identity.volume && t.links==1 && !t.directory && !same(i,t);close_native(target);}
        else target_safe=absent(os_error());
        if(target_safe)ok=relative_rename(h,q,dst,receipt_replace);
    }
    last_error=ok?0:os_error();close_native(h);
#else
    struct stat s{},t{};
    bool safe=fstatat(p,src.c_str(),&s,AT_SYMLINK_NOFOLLOW)==0 && S_ISREG(s.st_mode) && uint64_t(s.st_dev)==expected->second.volume && uint64_t(s.st_ino)==expected->second.file && s.st_nlink==1;
    bool target_safe=fstatat(q,dst.c_str(),&t,AT_SYMLINK_NOFOLLOW)<0?errno==ENOENT:S_ISREG(t.st_mode) && t.st_nlink==1;
    if(safe && target_safe)ok=syscall(SYS_renameat2,p,src.c_str(),q,dst.c_str(),receipt_replace?0:RENAME_NOREPLACE)==0;
    last_error=ok?0:os_error();
#endif
    close_native(p);close_native(q);
    if(ok){observations[b]=expected->second;observations.erase(a);}
    return result(ok,ok?"ok":"target_conflict");
}
Dictionary EquipmentSaveIO::acquire_lock(const String &tx) {
    std::string rel;if(!relative(tx,rel) || rel.empty() || !path_ok(tx))return result(false,"path_invalid");
    if(locks.count(rel))return result(true);
    auto h=open_file(rel+"/writer.lock",true,false);
    if(h==BAD_HANDLE)h=open_file(rel+"/writer.lock",false);
    if(h==BAD_HANDLE)return result(false,"busy");
    Identity i;if(!identity(h,i) || i.links!=1){close_native(h);return result(false,"busy");}
#ifdef _WIN32
    // 既存lockもread/writeに開く。LockFileExはhandleに結びつく。
    close_native(h);
    std::string leaf;auto directory=parent(rel+"/writer.lock",leaf);
    h=directory==BAD_HANDLE?BAD_HANDLE:relative_open(directory,leaf,GENERIC_READ|GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE,FILE_OPEN,FILE_NON_DIRECTORY_FILE);
    close_native(directory);
    Identity actual;OVERLAPPED position{};
    bool ok=h!=BAD_HANDLE && identity(h,actual) && same(i,actual) && actual.links==1 && LockFileEx(h,LOCKFILE_EXCLUSIVE_LOCK|LOCKFILE_FAIL_IMMEDIATELY,0,1,0,&position)!=0;
#else
    bool ok=flock(h,LOCK_EX|LOCK_NB)==0;
#endif
    last_error=ok?0:os_error();
    if(!ok){close_native(h);return result(false,"busy");}
    locks[rel]=h;return result(true);
}
String EquipmentSaveIO::legacy_link(const String &path) {
    // 唯一のlink読取り例外。旧053の監査参照名だけ返し、そのlinkをI/O対象として開かない。
    std::string rel;if(!relative(path,rel) || rel.find("/leases/lease-")==std::string::npos)return "";
#ifdef _WIN32
    return ""; // Windowsには旧053が作るPOSIX leaseがない。reparseは拒否。
#else
    std::string leaf;auto p=parent(rel,leaf);if(p<0)return "";
    char ref[256];auto count=readlinkat(p,leaf.c_str(),ref,sizeof(ref));close_native(p);
    if(count<=0 || count>=ssize_t(sizeof(ref)))return "";return String::utf8(ref,count);
#endif
}
int64_t EquipmentSaveIO::process_state(int64_t pid) {
    if(pid<=0)return -1;
#ifdef _WIN32
    if(uint64_t(pid)>MAXDWORD)return -1;
    auto h=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION|SYNCHRONIZE,FALSE,DWORD(pid));
    if(!h)return GetLastError()==ERROR_INVALID_PARAMETER?0:-1;
    auto status=WaitForSingleObject(h,0);close_native(h);return status==WAIT_OBJECT_0?0:status==WAIT_TIMEOUT?1:-1;
#else
    if(uint64_t(pid)>uint64_t(std::numeric_limits<pid_t>::max()))return -1;
    if(kill(pid,0)==0)return 1;return errno==ESRCH?0:-1;
#endif
}
void EquipmentSaveIO::_bind_methods() {
#define BIND(method, ...) ClassDB::bind_method(D_METHOD(#method, __VA_ARGS__),&EquipmentSaveIO::method)
    BIND(configure,"root");BIND(path_ok,"path");BIND(relative_path,"path");BIND(make_directories,"path");BIND(inspect_identity,"path");
    BIND(open_read,"path");BIND(read_all,"handle");BIND(open_write,"path","replace_tmp");BIND(write_exact,"handle","bytes");
    BIND(flush,"handle");BIND(close_file,"handle");BIND(rename_file,"from","to","receipt_replace");
    BIND(acquire_lock,"transaction");BIND(legacy_link,"path");BIND(process_state,"pid");
#undef BIND
}
extern "C" GDExtensionBool GDE_EXPORT equipment_save_io_init(GDExtensionInterfaceGetProcAddress proc,GDExtensionClassLibraryPtr library,GDExtensionInitialization *init) {
    GDExtensionBinding::InitObject object(proc,library,init);
    object.register_initializer([](ModuleInitializationLevel level){if(level==MODULE_INITIALIZATION_LEVEL_SCENE)ClassDB::register_class<EquipmentSaveIO>();});
    object.register_terminator([](ModuleInitializationLevel){});
    object.set_minimum_library_initialization_level(MODULE_INITIALIZATION_LEVEL_SCENE);return object.init();
}
