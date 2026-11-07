import os
import glob

def fix_all():
    cap_dir = 'tools/native-build/config/cap'
    
    # Extra pointers to ensure in BuiltinDirectives and JNIHeaderDirectives
    extra_pointers = {
        'BuiltinDirectives': [
            'char__', 'double_', 'double__', 'float_', 'float__',
            'graal_isolate_t__', 'graal_isolatethread_t__',
            'int__', 'long_long_', 'long_long__', 'short_', 'short__',
            'struct_JNIEnv___', 'struct_JavaVM___', 'void__'
        ],
        'JNIHeaderDirectives': [
            'char__', 'int__', 'void__', 'struct_JNINativeInterface___', 'struct_JNIInvokeInterface___'
        ]
    }
    
    for directive, ptrs in extra_pointers.items():
        cap_file = os.path.join(cap_dir, f'{directive}.cap')
        if not os.path.exists(cap_file):
            continue
        with open(cap_file, 'r') as fp:
            content = fp.read()
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        for p in ptrs:
            size_entry = f'NativeCodeInfo:{directive}:PointerToInfo:{p}:PropertyInfo:size=8'
            sign_entry = f'NativeCodeInfo:{directive}:PointerToInfo:{p}:PropertyInfo:signedness=$UNSIGNED$'
            if not any(l.startswith(f'NativeCodeInfo:{directive}:PointerToInfo:{p}:PropertyInfo:size=') for l in lines):
                lines.append(size_entry)
                lines.append(sign_entry)
                print(f'{directive}: added {p}')
        with open(cap_file, 'w', newline='\n') as fp:
            fp.write('\n'.join(lines) + '\n')

    # Now verify signedness on ALL PointerToInfo and ConstantInfo across all cap files
    cap_files = glob.glob(os.path.join(cap_dir, '*.cap'))
    signed_primitives = {'int', 'short', 'long_long', 'long_long_int', 'float', 'double', 'int32_t', 'int64_t'}

    for f in cap_files:
        with open(f, 'r') as fp:
            lines = [line.strip() for line in fp.read().splitlines() if line.strip()]
        
        new_lines = []
        modified = False
        seen_pointers = set()
        seen_constants = set()
        for l in lines:
            new_lines.append(l)
            if ':PointerToInfo:' in l and ':PropertyInfo:size=' in l:
                parts = l.split(':')
                p_idx = parts.index('PointerToInfo')
                directive = parts[1]
                type_name = parts[p_idx + 1]
                
                if (directive, type_name) in seen_pointers:
                    continue
                seen_pointers.add((directive, type_name))
                
                signed_prefix = f'NativeCodeInfo:{directive}:PointerToInfo:{type_name}:PropertyInfo:signedness='
                if not any(x.startswith(signed_prefix) for x in lines):
                    val = '$SIGNED$' if type_name in signed_primitives else '$UNSIGNED$'
                    new_line = f'NativeCodeInfo:{directive}:PointerToInfo:{type_name}:PropertyInfo:signedness={val}'
                    new_lines.append(new_line)
                    modified = True
                    print(f'{os.path.basename(f)}: added {new_line}')
            elif ':ConstantInfo:' in l and ':PropertyInfo:size=' in l:
                parts = l.split(':')
                c_idx = parts.index('ConstantInfo')
                directive = parts[1]
                const_name = parts[c_idx + 1]
                
                if (directive, const_name) in seen_constants:
                    continue
                seen_constants.add((directive, const_name))
                
                signed_prefix = f'NativeCodeInfo:{directive}:ConstantInfo:{const_name}:PropertyInfo:signedness='
                if not any(x.startswith(signed_prefix) for x in lines):
                    new_line = f'NativeCodeInfo:{directive}:ConstantInfo:{const_name}:PropertyInfo:signedness=$UNSIGNED$'
                    new_lines.append(new_line)
                    modified = True
                    print(f'{os.path.basename(f)}: added {new_line}')
                    
        if modified:
            with open(f, 'w', newline='\n') as fp:
                fp.write('\n'.join(new_lines) + '\n')

if __name__ == '__main__':
    fix_all()
