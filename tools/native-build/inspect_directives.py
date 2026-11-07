import os
import zipfile
import subprocess
import sys
import struct

def parse_class(data):
    if len(data) < 10:
        return None
    magic, minor, major, cp_count = struct.unpack('>IHHH', data[:10])
    if magic != 0xCAFEBABE:
        return None
    offset = 10
    cp = [None] * cp_count
    idx = 1
    while idx < cp_count:
        tag = data[offset]
        offset += 1
        if tag == 1: # Utf8
            length, = struct.unpack('>H', data[offset:offset+2])
            offset += 2
            val = data[offset:offset+length].decode('utf-8', errors='replace')
            offset += length
            cp[idx] = ('Utf8', val)
        elif tag in (3, 4): # Integer, Float
            offset += 4
            cp[idx] = ('Num', )
        elif tag in (5, 6): # Long, Double
            offset += 8
            cp[idx] = ('Num2', )
            idx += 1
        elif tag == 7: # Class
            name_idx, = struct.unpack('>H', data[offset:offset+2])
            offset += 2
            cp[idx] = ('Class', name_idx)
        elif tag == 8: # String
            offset += 2
            cp[idx] = ('String', )
        elif tag in (9, 10, 11): # Fieldref, Methodref, InterfaceMethodref
            offset += 4
            cp[idx] = ('Ref', )
        elif tag == 12: # NameAndType
            offset += 4
            cp[idx] = ('NameAndType', )
        elif tag == 15: # MethodHandle
            offset += 3
            cp[idx] = ('MethodHandle', )
        elif tag == 16: # MethodType
            offset += 2
            cp[idx] = ('MethodType', )
        elif tag in (17, 18): # Dynamic, InvokeDynamic
            offset += 4
            cp[idx] = ('Dynamic', )
        elif tag in (19, 20): # Module, Package
            offset += 2
            cp[idx] = ('ModPkg', )
        else:
            return None
        idx += 1
    
    access_flags, this_class, super_class, interfaces_count = struct.unpack('>HHHH', data[offset:offset+8])
    offset += 8
    interfaces = []
    for _ in range(interfaces_count):
        if_idx, = struct.unpack('>H', data[offset:offset+2])
        offset += 2
        if if_idx < len(cp) and cp[if_idx] and cp[if_idx][0] == 'Class':
            name_idx = cp[if_idx][1]
            if name_idx < len(cp) and cp[name_idx] and cp[name_idx][0] == 'Utf8':
                interfaces.append(cp[name_idx][1])
                
    this_name = ''
    if this_class < len(cp) and cp[this_class] and cp[this_class][0] == 'Class':
        name_idx = cp[this_class][1]
        if name_idx < len(cp) and cp[name_idx] and cp[name_idx][0] == 'Utf8':
            this_name = cp[name_idx][1]
            
    super_name = ''
    if super_class < len(cp) and cp[super_class] and cp[super_class][0] == 'Class':
        name_idx = cp[super_class][1]
        if name_idx < len(cp) and cp[name_idx] and cp[name_idx][0] == 'Utf8':
            super_name = cp[name_idx][1]

    return this_name, super_name, interfaces

def main():
    graal_home = os.environ.get('GRAALVM_HOME', os.environ.get('JAVA_HOME', ''))
    print(f"Scanning GraalVM for Directives classes at: {graal_home}")
    
    cap_dir = "tools/native-build/config/cap"
    os.makedirs(cap_dir, exist_ok=True)
    
    directives = set()
    
    for root, dirs, files in os.walk(graal_home):
        for f in files:
            if f.endswith('.jar'):
                jar_path = os.path.join(root, f)
                try:
                    with zipfile.ZipFile(jar_path) as z:
                        for name in z.namelist():
                            if not name.endswith('.class'):
                                continue
                            if 'Directives' not in name:
                                continue
                            try:
                                data = z.read(name)
                            except Exception:
                                continue
                            
                            parsed = parse_class(data)
                            if not parsed:
                                continue
                            this_name, super_name, interfaces = parsed
                            
                            is_directive = False
                            if 'org/graalvm/nativeimage/c/CContext$Directives' in interfaces:
                                is_directive = True
                            elif 'Directives' in this_name and not this_name.endswith('Feature') and not this_name.endswith('Processor') and not this_name.endswith('Support') and not this_name.endswith('Impl'):
                                is_directive = True
                                
                            if is_directive:
                                directives.add((jar_path, name))
                except Exception:
                    pass

    print(f"Total Directives classes confirmed: {len(directives)}")
    javap_bin = os.path.join(graal_home, 'bin', 'javap')
    
    for jar, name in sorted(directives, key=lambda x: x[1]):
        base_name = os.path.basename(name).replace('.class', '')
        simple_name = base_name.split('$')[-1]
        cap_name = f"{simple_name}.cap"
        cap_path = os.path.join(cap_dir, cap_name)
        has_cap = os.path.exists(cap_path)
        
        status = "exists" if has_cap else "MISSING -> CREATING"
        print(f"  {name} in {os.path.basename(jar)} -> {cap_name} ({status})")
        
        if not has_cap:
            with open(cap_path, 'a'):
                pass
            print(f"  [AUTO-CREATED] {cap_path}")
            
        class_name = name[:-6].replace('/', '.')
        if 'Locale' in name or 'Container' in name or 'JNI' in name:
            print(f"=== JAVAP FOR {class_name} ===")
            try:
                res = subprocess.run([javap_bin, '-p', '-cp', jar, class_name], capture_output=True, text=True)
                print(res.stdout)
            except Exception as e:
                print("javap error:", e)

if __name__ == '__main__':
    main()
