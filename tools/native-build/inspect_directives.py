import os
import zipfile
import subprocess
import sys

def main():
    graal_home = os.environ.get('GRAALVM_HOME', os.environ.get('JAVA_HOME', ''))
    print(f"Scanning GraalVM for Directives and CContext classes at: {graal_home}")
    
    cap_dir = "tools/native-build/config/cap"
    os.makedirs(cap_dir, exist_ok=True)
    
    directives = set()
    ccontext_annotated = set()
    
    for root, dirs, files in os.walk(graal_home):
        for f in files:
            if f.endswith('.jar'):
                jar_path = os.path.join(root, f)
                try:
                    with zipfile.ZipFile(jar_path) as z:
                        for name in z.namelist():
                            if not name.endswith('.class'):
                                continue
                            try:
                                data = z.read(name)
                            except Exception:
                                continue
                            
                            is_dir = False
                            if b'org/graalvm/nativeimage/c/CContext$Directives' in data:
                                is_dir = True
                            elif 'Directives' in name:
                                is_dir = True
                                
                            if is_dir:
                                directives.add((jar_path, name))
                                
                            if b'Lorg/graalvm/nativeimage/c/CContext;' in data:
                                ccontext_annotated.add((jar_path, name))
                except Exception:
                    pass

    print(f"Total Directives candidates found: {len(directives)}")
    print(f"Total CContext-annotated classes found: {len(ccontext_annotated)}")
    
    javap_bin = os.path.join(graal_home, 'bin', 'javap')
    
    for jar, name in sorted(directives, key=lambda x: x[1]):
        base_name = os.path.basename(name).replace('.class', '')
        # Handle inner classes if any: GraalVM simple name convention
        simple_name = base_name.split('$')[-1]
        cap_name = f"{simple_name}.cap"
        cap_path = os.path.join(cap_dir, cap_name)
        has_cap = os.path.exists(cap_path)
        
        status = "exists" if has_cap else "MISSING -> CREATING"
        print(f"  {name} in {os.path.basename(jar)} -> {cap_name} ({status})")
        
        if not has_cap:
            # Auto-create empty cap file so Native Image doesn't crash on missing file
            with open(cap_path, 'a'):
                pass
            print(f"  [AUTO-CREATED] {cap_path}")
            
        class_name = name[:-6].replace('/', '.')
        # If it's a locale or container or newly created cap, javap it for diagnostics
        if 'Locale' in name or 'Container' in name or not has_cap:
            print(f"=== JAVAP FOR {class_name} ===")
            try:
                res = subprocess.run([javap_bin, '-p', '-cp', jar, class_name], capture_output=True, text=True)
                print(res.stdout)
            except Exception as e:
                print("javap error:", e)

    # Also log any classes in com/oracle/svm/core/c/locale
    print("=== Scanning locale package classes ===")
    for jar, name in sorted(ccontext_annotated, key=lambda x: x[1]):
        if 'locale' in name.lower():
            class_name = name[:-6].replace('/', '.')
            print(f"Locale class: {class_name} in {os.path.basename(jar)}")
            try:
                res = subprocess.run([javap_bin, '-p', '-cp', jar, class_name], capture_output=True, text=True)
                print(res.stdout)
            except Exception as e:
                print("javap error:", e)

if __name__ == '__main__':
    main()
