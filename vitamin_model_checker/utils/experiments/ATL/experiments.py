import math
import random
import sys
sys.path.append('/media/angelo/WorkData/git/VITAMIN')
from vitamin_model_checker.model_checker_interface.explicit import ATL
from vitamin_model_checker.utils.generators import CGS_generator
import time
import concurrent.futures

TIMEOUT = 300  # 5 minutes

def run_experiments(num_agents_min, num_agents_max, num_states_min, num_states_max, repetitions):
    with open('results.csv', 'w') as file:
        file.write('# States; # Agents; ATL time [sec]\n')    
    for state in range(num_states_min, num_states_max+1, 10):
        for agents in range(num_agents_min, num_agents_max+1):
            coalition = ','.join([str(i) for i in range(1, agents+1)])
            # target = f'a1{random.randint(1, int(math.sqrt(state)))}_{random.randint(1, int(math.sqrt(state)))}'
            target = 'a11_1'
            phi = f'(<{coalition}>F {target})'
            avg_time = 0
            with open('results.csv', 'a') as file:
                file.write(str(state) + ';' + str(agents) + ';')
            for _ in range(0, repetitions):
                CGS_generator.generate_random_CGS(agents, int(math.sqrt(state)), int(math.sqrt(state)), random.randint(1, int(math.sqrt(state))), 'tmp')
                # Measure start time
                start = time.time()
                # Use a ThreadPoolExecutor to handle the timeout
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    # Submit the model_checking task to the executor
                    future = executor.submit(ATL.model_checking, phi, 'tmp')
                    try:
                        # Wait for the result with a specified timeout
                        res = future.result(timeout=TIMEOUT)
                    except concurrent.futures.TimeoutError:
                        # Handle timeout situation
                        print("model_checking took too long and was terminated.")
                        res = None  # Or handle as needed
                # Measure end time
                end = time.time()
                avg_time += end-start
            avg_time = avg_time / repetitions
            with open('results.csv', 'a') as file:
                file.write(str(avg_time) + '\n')

if __name__ == "__main__":
    num_agents_min = max(int(sys.argv[1]), 1)
    num_agents_max = max(int(sys.argv[2]), 1)
    num_states_min = max(int(sys.argv[3]), 1)
    num_states_max = max(int(sys.argv[4]), 1)
    repetitions = max(int(sys.argv[5]), 1)
    run_experiments(num_agents_min, num_agents_max, num_states_min, num_states_max, repetitions)


