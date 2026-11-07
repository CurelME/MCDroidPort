import os
import glob

def fix_signedness():
    cap_dir = 'tools/native-build/config/cap'
    cap_files = glob.glob(os.path.join(cap_dir, '*.cap'))

    signed_primitives = {'int', 'short', 'long_long', 'long_long_int', 'float', 'double', 'int32_t', 'int64_t'}

    for f in cap_files:
        with open(f, 'r') as fp:
            lines = [line.strip() for line in fp if line.strip()]
        
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
                    if type_name in signed_primitives:
                        val = '$SIGNED$'
                    else:
                        val = '$UNSIGNED$'
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
                    val = '$UNSIGNED$'
                    new_line = f'NativeCodeInfo:{directive}:ConstantInfo:{const_name}:PropertyInfo:signedness={val}'
                    new_lines.append(new_line)
                    modified = True
                    print(f'{os.path.basename(f)}: added {new_line}')
                    
        if modified:
            with open(f, 'w') as fp:
                fp.write('\n'.join(new_lines) + '\n')

if __name__ == '__main__':
    fix_signedness()
