#!/usr/bin/env python3
"""
SQLAlchemy Relationship Audit Script
Scans all model files and identifies missing or misconfigured relationships.
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class RelationshipAuditor:
    def __init__(self, models_dir: str):
        self.models_dir = Path(models_dir)
        self.relationships = defaultdict(list)  # {ModelName: [(target, back_populates, line_num)]}
        self.classes = {}  # {ModelName: filepath}
        self.issues = []

    def scan_models(self):
        """Scan all Python files in the models directory."""
        for py_file in self.models_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            self._parse_file(py_file)

    def _parse_file(self, filepath: Path):
        """Parse a Python file to extract class names and relationships."""
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            # Find class definitions
            class_pattern = r'class\s+(\w+)\s*\('
            for match in re.finditer(class_pattern, content):
                class_name = match.group(1)
                if class_name != 'Base':
                    self.classes[class_name] = str(filepath)

            # Find relationship declarations
            rel_pattern = r'(\w+)\s*=\s*relationship\s*\(\s*["\']([^"\']+)["\']\s*(?:,.*?back_populates\s*=\s*["\']([^"\']+)["\'])?'

            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                matches = re.finditer(rel_pattern, line)
                for match in matches:
                    attr_name = match.group(1)
                    target_class = match.group(2)
                    back_populates = match.group(3) if match.group(3) else None

                    # Find which class this relationship belongs to
                    for class_match in re.finditer(class_pattern, content[:content.find(line)]):
                        current_class = class_match.group(1)

                    if current_class and current_class != 'Base':
                        # Clean target class name (remove module paths)
                        target_class = target_class.split('.')[-1]
                        self.relationships[current_class].append({
                            'attribute': attr_name,
                            'target': target_class,
                            'back_populates': back_populates,
                            'line': i,
                            'file': str(filepath)
                        })
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")

    def audit(self):
        """Audit all relationships and identify issues."""
        print("=" * 80)
        print("SQLALCHEMY RELATIONSHIP AUDIT REPORT")
        print("=" * 80)
        print()

        # Check for missing back_populates
        print("1. Relationships Missing back_populates:")
        print("-" * 80)
        missing_back_populates = []
        for model, rels in self.relationships.items():
            for rel in rels:
                if not rel['back_populates']:
                    missing_back_populates.append(rel)
                    print(f"  {model}.{rel['attribute']} -> {rel['target']}")
                    print(f"    File: {rel['file']}:{rel['line']}")

        if not missing_back_populates:
            print("  ✓ All relationships have back_populates defined")
        print()

        # Check for missing reverse relationships
        print("2. Missing Reverse Relationships:")
        print("-" * 80)
        missing_reverse = []
        for model, rels in self.relationships.items():
            for rel in rels:
                if rel['back_populates']:
                    target = rel['target']
                    back_pop = rel['back_populates']

                    # Check if target class has the reverse relationship
                    if target in self.relationships:
                        target_rels = self.relationships[target]
                        found = False
                        for target_rel in target_rels:
                            if target_rel['attribute'] == back_pop:
                                found = True
                                break

                        if not found:
                            missing_reverse.append({
                                'source_model': model,
                                'source_attr': rel['attribute'],
                                'target_model': target,
                                'expected_attr': back_pop,
                                'file': self.classes.get(target, 'UNKNOWN')
                            })
                            print(f"  {model}.{rel['attribute']} expects {target}.{back_pop}")
                            print(f"    Missing in: {self.classes.get(target, 'UNKNOWN')}")
                    else:
                        print(f"  WARNING: Target class '{target}' not found for {model}.{rel['attribute']}")

        if not missing_reverse:
            print("  ✓ All reverse relationships exist")
        print()

        # Check for type mismatches
        print("3. Relationship Configuration Summary:")
        print("-" * 80)
        for model in sorted(self.relationships.keys()):
            print(f"\n  {model}:")
            for rel in self.relationships[model]:
                status = "✓" if rel['back_populates'] else "✗"
                print(f"    {status} {rel['attribute']} -> {rel['target']}")
                if rel['back_populates']:
                    print(f"      (back_populates: {rel['back_populates']})")
        print()

        # Generate fix recommendations
        print("=" * 80)
        print("FIX RECOMMENDATIONS")
        print("=" * 80)
        print()

        if missing_reverse:
            print("Add these relationships to fix missing reverse references:")
            print()

            fixes_by_file = defaultdict(list)
            for issue in missing_reverse:
                fixes_by_file[issue['file']].append(issue)

            for filepath, issues in fixes_by_file.items():
                print(f"File: {filepath}")
                for issue in issues:
                    print(f"  Add to {issue['target_model']}:")
                    print(f"    {issue['expected_attr']} = relationship(")
                    print(f"        \"{issue['source_model']}\",")
                    print(f"        back_populates=\"{issue['source_attr']}\",")
                    print(f"        lazy=\"select\"")
                    print(f"    )")
                print()

        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Models: {len(self.classes)}")
        print(f"Total Relationships: {sum(len(rels) for rels in self.relationships.values())}")
        print(f"Missing back_populates: {len(missing_back_populates)}")
        print(f"Missing Reverse Relationships: {len(missing_reverse)}")
        print()

        if missing_reverse:
            print("❌ Issues found that need fixing")
            return False
        else:
            print("✅ All relationships are correctly configured")
            return True

if __name__ == "__main__":
    import sys

    models_dir = sys.argv[1] if len(sys.argv) > 1 else "src/models"

    auditor = RelationshipAuditor(models_dir)
    auditor.scan_models()
    success = auditor.audit()

    sys.exit(0 if success else 1)
