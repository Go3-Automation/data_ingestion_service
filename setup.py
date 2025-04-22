from setuptools import setup, find_packages

setup(
    name='data_ingestion',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests',
        'botocore',
    ],
    author='Michal Pajak',
    description='A service for data ingestion API to DIIP',
    url='https://github.com/Go3-Automation/data_ingestion_service',  
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: Other/Proprietary License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    license='Custom License for Go3',
)