#!/usr/bin/env python3
"""
Test script to check memory usage of the API components
"""
import psutil
import os
import sys

def get_memory_usage():
    """Get current memory usage"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / 1024 / 1024  # Convert to MB

print(f"Initial memory usage: {get_memory_usage():.2f} MB")

# Test importing each dependency
print("Testing imports...")

print(f"Before FastAPI: {get_memory_usage():.2f} MB")
from fastapi import FastAPI
print(f"After FastAPI: {get_memory_usage():.2f} MB")

print(f"Before Pydantic: {get_memory_usage():.2f} MB")
from pydantic import BaseModel
print(f"After Pydantic: {get_memory_usage():.2f} MB")

print(f"Before NumPy: {get_memory_usage():.2f} MB")
import numpy as np
print(f"After NumPy: {get_memory_usage():.2f} MB")

print(f"Before Pandas: {get_memory_usage():.2f} MB")
import pandas as pd
print(f"After Pandas: {get_memory_usage():.2f} MB")

print(f"Before Scikit-learn: {get_memory_usage():.2f} MB")
import sklearn
print(f"After Scikit-learn: {get_memory_usage():.2f} MB")

print(f"Before Joblib: {get_memory_usage():.2f} MB")
import joblib
print(f"After Joblib: {get_memory_usage():.2f} MB")

# Test loading a simple model if available
if os.path.exists('model.pkl'):
    print(f"Before loading model: {get_memory_usage():.2f} MB")
    try:
        model = joblib.load('model.pkl')
        print(f"After loading model: {get_memory_usage():.2f} MB")
    except Exception as e:
        print(f"Error loading model: {e}")

print(f"Final memory usage: {get_memory_usage():.2f} MB")