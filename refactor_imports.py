import os
import re

def resolve_relative_path(current_file_path, target_alias_path):
    # current_file_path: e.g., "frontend/src/app/optimizer/page.tsx"
    # target_alias_path: e.g., "@/lib/api" (which maps to "frontend/src/lib/api")
    
    # We assume the root of the frontend is "frontend"
    # And specifically, the alias "@/" maps to "frontend/src/"
    
    # Get the directory of the current file
    current_dir = os.path.dirname(current_file_path)
    
    # Determine the absolute path of the target (assuming script run from project root)
    # Remove "@/" and prepend "frontend/src/"
    target_path_suffix = target_alias_path[2:] # "lib/api"
    target_abs_path = os.path.abspath(os.path.join("frontend/src", target_path_suffix))
    
    # Get absolute path of current dir
    current_abs_dir = os.path.abspath(current_dir)
    
    # Calculate relative path
    rel_path = os.path.relpath(target_abs_path, current_abs_dir)
    
    if not rel_path.startswith("."):
        rel_path = "./" + rel_path
        
    return rel_path

def refactor_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Regex to find imports using "@/"
    # Matches: import X from "@/..." or import { X } from "@/..."
    # capture group 1: the quote (either ' or ")
    # capture group 2: the path starting with @/
    pattern = r'(from\s+)(["\'])(@/[^"\']+)(["\'])'
    
    def replacer(match):
        prefix = match.group(1)
        quote = match.group(2)
        alias_path = match.group(3)
        end_quote = match.group(4)
        
        relative_path = resolve_relative_path(file_path, alias_path)
        print(f"Refactoring {file_path}: {alias_path} -> {relative_path}")
        return f"{prefix}{quote}{relative_path}{end_quote}"
    
    new_content = re.sub(pattern, replacer, content)
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)

def main():
    root_dir = "frontend/src"
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".ts") or filename.endswith(".tsx"):
                file_path = os.path.join(dirpath, filename)
                refactor_file(file_path)

if __name__ == "__main__":
    main()
