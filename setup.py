'''
This file is used for packaging and distributing
Python projects. It's used by setuptools to define
configuration of this project.
'''

from setuptools import find_packages, setup
from typing import List

def get_requirements(file_path: str) -> List[str]:
  '''
  Reads a requirements file and returns a list of requirements.
  '''
  requirements_list: List[str] = []
  try:
    with open("requirements.txt", "r") as file:
      # Read lines from the file
      lines = file.readlines()
      
      # Process each line
      for line in lines:
        requirements = line.strip()
        # Ignore the empty line and -e .
        if requirements and requirements != "-e .":
          requirements_list.append(requirements)
  except FileNotFoundError:
    print(f"Warning: {file_path} not found. No requirements will be added.")
  return requirements_list

setup(
  name="Smartphone Battery Backend Dashboard",
  version="0.1.0",
  author="Fadel Achmad Daniswara",
  author_email="daniswarafadel@gmail.com",
  packages=find_packages(),
  install_requires=get_requirements(),
)