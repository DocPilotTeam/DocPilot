import os
def generate_tree(root_dir: str, prefix: str = "") -> list[str]:
    entries = sorted(
        e for e in os.listdir(root_dir)
        if e not in {".git", "__pycache__"}
    )

    lines = []

    for i, entry in enumerate(entries):
        path = os.path.join(root_dir, entry)
        is_last = i == len(entries) - 1

        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + entry)

        if os.path.isdir(path):
            extension = "    " if is_last else "│   "
            lines.extend(generate_tree(path, prefix + extension))

    return lines


def generate_directory_tree(base_path: str, root_name: str | None = None) -> str:
    root_label = root_name or os.path.basename(base_path.rstrip("/"))
    output = [f"{root_label}/"]
    output.extend(generate_tree(base_path))
    return "\n".join(output)
