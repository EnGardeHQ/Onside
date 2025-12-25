#!/usr/bin/env python
"""
Verification script for I18nAwareChainOfThought implementation.

This script verifies that the core I18nAwareChainOfThought class was implemented
correctly and follows the requirements for Sprint 5 internationalization.

Following Semantic Seed coding standards with proper error handling.
"""
import os
import sys
import inspect
import importlib.util
from typing import List, Dict, Any

# Core verification functions
def verify_class_exists(path, class_name) -> bool:
    """Verify that a class exists and can be imported."""
    try:
        # Extract directory and filename
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        module_name = os.path.splitext(filename)[0]
        
        # Add directory to path if needed
        if directory and directory not in sys.path:
            sys.path.insert(0, directory)
            
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check if class exists
        return hasattr(module, class_name)
    except Exception as e:
        print(f"Error importing {path}: {e}")
        return False

def verify_methods_exist(path, class_name, required_methods) -> Dict[str, bool]:
    """Verify that required methods exist in a class."""
    results = {}
    
    try:
        # Extract directory and filename
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        module_name = os.path.splitext(filename)[0]
        
        # Add directory to path if needed
        if directory and directory not in sys.path:
            sys.path.insert(0, directory)
            
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the class
        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            
            # Check each required method
            for method_name in required_methods:
                if hasattr(cls, method_name):
                    # Verify it's a method, not an attribute
                    attribute = getattr(cls, method_name)
                    if callable(attribute):
                        results[method_name] = True
                    else:
                        results[method_name] = False
                        print(f"'{method_name}' is not callable")
                else:
                    results[method_name] = False
                    print(f"'{method_name}' not found in {class_name}")
        else:
            for method_name in required_methods:
                results[method_name] = False
            print(f"Class {class_name} not found in {path}")
    except Exception as e:
        print(f"Error checking methods in {path}: {e}")
        for method_name in required_methods:
            results[method_name] = False
            
    return results

def verify_method_parameters(path, class_name, method_name, required_parameters) -> Dict[str, bool]:
    """Verify that a method has required parameters."""
    results = {}
    
    try:
        # Extract directory and filename
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        module_name = os.path.splitext(filename)[0]
        
        # Add directory to path if needed
        if directory and directory not in sys.path:
            sys.path.insert(0, directory)
            
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the class and method
        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            
            if hasattr(cls, method_name):
                method = getattr(cls, method_name)
                
                # Get the signature
                sig = inspect.signature(method)
                parameters = list(sig.parameters.keys())
                
                # Check each required parameter
                for param in required_parameters:
                    if param in parameters:
                        results[param] = True
                    else:
                        results[param] = False
                        print(f"Parameter '{param}' not found in {method_name}")
            else:
                for param in required_parameters:
                    results[param] = False
                print(f"Method {method_name} not found in {class_name}")
        else:
            for param in required_parameters:
                results[param] = False
            print(f"Class {class_name} not found in {path}")
    except Exception as e:
        print(f"Error checking parameters in {path}: {e}")
        for param in required_parameters:
            results[param] = False
            
    return results

def verify_integration_methods(path, class_name, method_name) -> bool:
    """Verify that the I18nFramework has methods to create I18nAwareChainOfThought."""
    try:
        # Extract directory and filename
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        module_name = os.path.splitext(filename)[0]
        
        # Add directory to path if needed
        if directory and directory not in sys.path:
            sys.path.insert(0, directory)
            
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check if class and method exist
        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            
            if hasattr(cls, method_name):
                method = getattr(cls, method_name)
                
                # Check if it's a method
                if callable(method):
                    return True
                else:
                    print(f"'{method_name}' is not callable")
                    return False
            else:
                print(f"Method {method_name} not found in {class_name}")
                return False
        else:
            print(f"Class {class_name} not found in {path}")
            return False
    except Exception as e:
        print(f"Error checking integration in {path}: {e}")
        return False

# Main verification function
def verify_i18n_ai_implementation():
    """Verify the I18nAwareChainOfThought implementation."""
    print("\n===== Verifying I18nAwareChainOfThought Implementation =====\n")
    
    # Paths to files
    i18n_chain_path = "/Users/tobymorning/OnSide/src/services/ai/i18n_chain_of_thought.py"
    i18n_integration_path = "/Users/tobymorning/OnSide/src/services/i18n/integration.py"
    
    # Class and method names
    i18n_chain_class = "I18nAwareChainOfThought"
    i18n_framework_class = "I18nFramework"
    factory_method = "create_i18n_ai_service"
    
    # Required methods
    required_methods = [
        "execute_multilingual_prompt",
        "translate_llm_result",
        "execute_with_language",
        "_translate_dict_recursively"
    ]
    
    # Required parameters
    required_execute_params = [
        "template_id",
        "language",
        "variables",
        "report"
    ]
    
    required_translate_params = [
        "result",
        "target_language"
    ]
    
    # Verification results
    results = {
        "class_exists": False,
        "methods_exist": {},
        "parameters_exist": {},
        "integration_exists": False
    }
    
    # 1. Verify the class exists
    print("Checking if I18nAwareChainOfThought class exists...")
    results["class_exists"] = verify_class_exists(i18n_chain_path, i18n_chain_class)
    if results["class_exists"]:
        print("✅ I18nAwareChainOfThought class exists")
    else:
        print("❌ I18nAwareChainOfThought class not found")
    
    # 2. Verify required methods exist
    print("\nChecking if required methods exist...")
    results["methods_exist"] = verify_methods_exist(i18n_chain_path, i18n_chain_class, required_methods)
    
    all_methods_exist = all(results["methods_exist"].values())
    if all_methods_exist:
        print("✅ All required methods exist")
    else:
        print("❌ Some required methods are missing")
        
    # 3. Verify method parameters
    print("\nChecking if execute_multilingual_prompt has required parameters...")
    results["parameters_exist"]["execute"] = verify_method_parameters(
        i18n_chain_path, 
        i18n_chain_class, 
        "execute_multilingual_prompt", 
        required_execute_params
    )
    
    all_execute_params_exist = all(results["parameters_exist"]["execute"].values())
    if all_execute_params_exist:
        print("✅ execute_multilingual_prompt has all required parameters")
    else:
        print("❌ execute_multilingual_prompt is missing some parameters")
    
    print("\nChecking if translate_llm_result has required parameters...")
    results["parameters_exist"]["translate"] = verify_method_parameters(
        i18n_chain_path, 
        i18n_chain_class, 
        "translate_llm_result", 
        required_translate_params
    )
    
    all_translate_params_exist = all(results["parameters_exist"]["translate"].values())
    if all_translate_params_exist:
        print("✅ translate_llm_result has all required parameters")
    else:
        print("❌ translate_llm_result is missing some parameters")
    
    # 4. Verify integration with I18nFramework
    print("\nChecking if I18nFramework can create I18nAwareChainOfThought...")
    results["integration_exists"] = verify_integration_methods(
        i18n_integration_path, 
        i18n_framework_class, 
        factory_method
    )
    
    if results["integration_exists"]:
        print("✅ I18nFramework can create I18nAwareChainOfThought")
    else:
        print("❌ I18nFramework integration is missing")
    
    # Overall result
    print("\n===== Verification Results =====\n")
    
    all_passed = (
        results["class_exists"] and
        all_methods_exist and
        all_execute_params_exist and
        all_translate_params_exist and
        results["integration_exists"]
    )
    
    if all_passed:
        print("✅ I18nAwareChainOfThought implementation PASSES all checks!")
        print("   All required classes, methods, parameters, and integrations are present.")
    else:
        print("❌ I18nAwareChainOfThought implementation FAILS some checks.")
        print("   Please fix the issues noted above.")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = verify_i18n_ai_implementation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error during verification: {e}")
        sys.exit(1)
