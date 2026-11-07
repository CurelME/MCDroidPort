import os
import glob

def fix_all():
    cap_dir = 'tools/native-build/config/cap'
    
    standard_primitives = [
        ('unsigned_char', 1, '$UNSIGNED$'),
        ('signed_char', 1, '$SIGNED$'),
        ('unsigned_short', 2, '$UNSIGNED$'),
        ('unsigned_int', 4, '$UNSIGNED$'),
        ('long', 8, '$SIGNED$'),
        ('unsigned_long', 8, '$UNSIGNED$'),
        ('unsigned_long_long', 8, '$UNSIGNED$'),
        ('bool', 1, '$UNSIGNED$'),
        ('_Bool', 1, '$UNSIGNED$'),
        ('int8_t', 1, '$SIGNED$'),
        ('uint8_t', 1, '$UNSIGNED$'),
        ('int16_t', 2, '$SIGNED$'),
        ('uint16_t', 2, '$UNSIGNED$'),
        ('int32_t', 4, '$SIGNED$'),
        ('uint32_t', 4, '$UNSIGNED$'),
        ('int64_t', 8, '$SIGNED$'),
        ('uint64_t', 8, '$UNSIGNED$'),
        ('size_t', 8, '$UNSIGNED$'),
        ('ssize_t', 8, '$SIGNED$'),
        ('intptr_t', 8, '$SIGNED$'),
        ('uintptr_t', 8, '$UNSIGNED$'),
        ('ptrdiff_t', 8, '$SIGNED$'),
    ]

    target_directives = ['BuiltinDirectives', 'JNIHeaderDirectives', 'PosixDirectives', 'LocaleDirectives']
    for directive in target_directives:
        cap_file = os.path.join(cap_dir, f'{directive}.cap')
        if not os.path.exists(cap_file):
            continue
        with open(cap_file, 'r') as fp:
            lines = [l.strip() for l in fp.read().splitlines() if l.strip()]
        
        for name, sz, sign in standard_primitives:
            for variant, var_sz, var_sign in [(name, sz, sign), (f'{name}_', 8, '$UNSIGNED$'), (f'{name}__', 8, '$UNSIGNED$')]:
                size_entry = f'NativeCodeInfo:{directive}:PointerToInfo:{variant}:PropertyInfo:size={var_sz}'
                sign_entry = f'NativeCodeInfo:{directive}:PointerToInfo:{variant}:PropertyInfo:signedness={var_sign}'
                if not any(l.startswith(f'NativeCodeInfo:{directive}:PointerToInfo:{variant}:PropertyInfo:size=') for l in lines):
                    lines.append(size_entry)
                    lines.append(sign_entry)
                    print(f'{directive}: added {variant}')
        with open(cap_file, 'w', newline='\n') as fp:
            fp.write('\n'.join(lines) + '\n')

    extra_pointers = {
        'BuiltinDirectives': [
            'char__', 'double_', 'double__', 'float_', 'float__',
            'graal_isolate_t__', 'graal_isolatethread_t__',
            'int__', 'long_long_', 'long_long__', 'short_', 'short__',
            'struct_JNIEnv___', 'struct_JavaVM___', 'void__'
        ],
        'JNIHeaderDirectives': [
            'struct__jfieldID_', 'struct__jfieldID__',
            'struct__jmethodID_', 'struct__jmethodID__',
            'struct__jobject_', 'struct__jobject__',
            'struct__jclass_', 'struct__jclass__',
            'struct__jthrowable_', 'struct__jthrowable__',
            'struct__jstring_', 'struct__jstring__',
            'struct__jarray_', 'struct__jarray__',
            'struct__jbooleanArray_', 'struct__jbooleanArray__',
            'struct__jbyteArray_', 'struct__jbyteArray__',
            'struct__jcharArray_', 'struct__jcharArray__',
            'struct__jshortArray_', 'struct__jshortArray__',
            'struct__jintArray_', 'struct__jintArray__',
            'struct__jlongArray_', 'struct__jlongArray__',
            'struct__jfloatArray_', 'struct__jfloatArray__',
            'struct__jdoubleArray_', 'struct__jdoubleArray__',
            'struct__jobjectArray_', 'struct__jobjectArray__',
            'struct__jweak_', 'struct__jweak__',
            'jboolean_', 'jboolean__',
            'jbyte_', 'jbyte__',
            'jchar_', 'jchar__',
            'jshort_', 'jshort__',
            'jint_', 'jint__',
            'jlong_', 'jlong__',
            'jfloat_', 'jfloat__',
            'jdouble_', 'jdouble__',
            'jsize_', 'jsize__',
            'char__', 'int__', 'void__',
            'struct_JNINativeInterface___', 'struct_JNIInvokeInterface___',
            'struct_JNIEnv___', 'struct_JavaVM___'
        ]
    }
    
    for directive, ptrs in extra_pointers.items():
        cap_file = os.path.join(cap_dir, f'{directive}.cap')
        if not os.path.exists(cap_file):
            continue
        with open(cap_file, 'r') as fp:
            lines = [l.strip() for l in fp.read().splitlines() if l.strip()]
        for p in ptrs:
            size_entry = f'NativeCodeInfo:{directive}:PointerToInfo:{p}:PropertyInfo:size=8'
            sign_entry = f'NativeCodeInfo:{directive}:PointerToInfo:{p}:PropertyInfo:signedness=$UNSIGNED$'
            if not any(l.startswith(f'NativeCodeInfo:{directive}:PointerToInfo:{p}:PropertyInfo:size=') for l in lines):
                lines.append(size_entry)
                lines.append(sign_entry)
                print(f'{directive}: added {p}')
        with open(cap_file, 'w', newline='\n') as fp:
            fp.write('\n'.join(lines) + '\n')

    # Verify signedness on ALL PointerToInfo and ConstantInfo across all cap files
    cap_files = glob.glob(os.path.join(cap_dir, '*.cap'))
    signed_primitives = {'int', 'short', 'long_long', 'long_long_int', 'float', 'double', 'int32_t', 'int64_t', 'signed_char', 'ssize_t', 'int8_t', 'int16_t', 'intptr_t', 'ptrdiff_t', 'long'}

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
                    val = '$SIGNED$' if type_name in signed_primitives and not type_name.endswith('_') else '$UNSIGNED$'
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
