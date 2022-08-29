from setuptools import setup, find_packages, find_namespace_packages

setup(name='asmregex',
      version='0.2.1',
      description='Matching regular expressions on asm code',
      url='https://outoftheheap.com/',
      author='Jordy Gennissen',
      author_email='jordy.gennissen@rhul.ac.uk',
      license='CC 3.0 Non-commercial',
      packages=find_namespace_packages(),  #['asmregex'],
      install_requires =['angr', 'numpy'], # angr or r2pipe, depending on the user
      dependency_links=[],
      zip_safe=False)
