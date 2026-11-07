import os
import zipfile
import subprocess
import sys

def main():
    graal_home = os.environ.get('GRAALVM_HOME', os.environ.get('JAVA_HOME', ''))
    print(f"Scanning GraalVM for Directives classes at: {graal_home}")
    directives = set()
    for root, dirs, files in os.walk(graal_home):
        for f in files:
            if f.endswith('.jar'):
                jar_path = os.path.join(root, f)
                try:
                    with zipfile.ZipFile(jar_path) as z:
                        for name in z.namelist():
                            if 'Directives' in name and name.endswith('.class') and not '$' in name:
                                directives.add((jar_path, name))
                except Exception:
                    pass

    print(f"Total top-level Directives classes found: {len(directives)}")
    cap_dir = "tools/native-build/config/cap"
    for jar, name in sorted(directives, key=lambda x: x[1]):
        base_name = os.path.basename(name)
        cap_name = base_name.replace('.class', '.cap')
        cap_path = os.path.join(cap_dir, cap_name)
        has_cap = os.path.exists(cap_path)
        print(f"  {name} in {os.path.basename(jar)} -> {cap_name} (exists={has_cap})")
        if 'Container' in name or not has_cap:
            class_name = name[:-6].replace('/', '.')
            print(f"=== JAVAP FOR {class_name} ===")
            javap_bin = os.path.join(graal_home, 'bin', 'javap')
            try:
                res = subprocess.run([javap_bin, '-p', '-cp', jar, class_name], capture_output=True, text=True)
                print(res.stdout)
            except Exception as e:
                print("javap error:", e)

if __name__ == '__main__':
    main()
