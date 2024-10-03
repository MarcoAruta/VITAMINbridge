from setuptools import setup, find_packages

# Function to read the requirements.txt file
def parse_requirements(filename):
    with open(filename) as f:
        return f.read().splitlines()
  
setup( 
    name='vitamin-model-checker-test', 
    version='1.0', 
    description='The VITAMIN model checker python package', 
    long_description='VITAMIN is an open-source model checker tailored to the verification of Multi-Agent Systems (MAS). MAS descriptions are given by means of labelled transition systems.',
    author='Angelo Ferrando', 
    author_email='angelo.ferrando42@gmail.com', 
    packages=[
        'vitamin_model_checker', 
        'vitamin_model_checker.logics',
        'vitamin_model_checker.logics.ATL', 
        'vitamin_model_checker.logics.CapATL',
        'vitamin_model_checker.logics.CTL',
        'vitamin_model_checker.logics.NatATL',
        'vitamin_model_checker.logics.OATL',
        'vitamin_model_checker.logics.OL',
        'vitamin_model_checker.logics.RABATL',
        'vitamin_model_checker.logics.RBATL',
        'vitamin_model_checker.model_checker_interface',
        'vitamin_model_checker.model_checker_interface.explicit',
        'vitamin_model_checker.model_checker_interface.explicit.ATL',
        'vitamin_model_checker.model_checker_interface.explicit.ATLF',
        'vitamin_model_checker.model_checker_interface.explicit.CapATL',
        'vitamin_model_checker.model_checker_interface.explicit.CTL',
        'vitamin_model_checker.model_checker_interface.explicit.NatATL',
        'vitamin_model_checker.model_checker_interface.explicit.OATL',
        'vitamin_model_checker.model_checker_interface.explicit.OL',
        'vitamin_model_checker.model_checker_interface.explicit.RABATL',
        'vitamin_model_checker.model_checker_interface.explicit.RBATL', 
        'vitamin_model_checker.model_checker_interface.implicit', 
        'vitamin_model_checker.model_checker_interface.abstract', 
        'vitamin_model_checker.models',
        'vitamin_model_checker.models.capCGS',
        'vitamin_model_checker.models.CGS',
        'vitamin_model_checker.models.costCGS'
    ],
    install_requires=parse_requirements('requirements.txt') 
) 
