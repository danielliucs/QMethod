import gym
import collections
from tensorboardX import SummaryWriter

ENV_NAME = "FrozenLake-v0"
GAMMA = 0.9
TEST_EPISODES = 20

class Agent:
    def __init__(self):
        self.env = gym.make(ENV_NAME)
        self.state = self.env.reset()
        self.rewards = collections.defaultdict(float)
        self.transits = collections.defaultdict(collections.Counter)
        self.values = collections.defaultdict(float)

    #Used to gather random experience from the environemnt and update reward and transition tables
    #Notice how it can learn mid episode
    def play_n_random_steps(self, count):
        for _ in range(count):
            action = self.env.action_space.sample()
            new_state, reward, is_done, extra_info = self.env.step(action)
            self.rewards[(self.state, action, new_state)] = reward #reward table, composite key
            self.transits[(self.state, action)][new_state] += 1 #transition table, composite key with another dictionary and counter
            self.state = self.env.reset() if is_done else new_state
    
    #Calculates the value of the action from state using transition, reward, and values tables
    def calc_action_value(self, state, action):
        #Extract transition counters for the given state and action
        target_counts = self.transits[(state,action)]
        #Sum all counters to obtain total count of times action executes from state
        total = sum(target_counts.values())
        action_value = 0.0
        for tgt_state, count in target_counts.items():
            #Calculate immediate award
            reward = self.rewards[(state, action, tgt_state)]
            #Bellman equation, count/total is probability
            action_value += (count / total) * (reward + GAMMA * self.values[tgt_state])
        return action_value
        #Graph for visual under issues->images

    #Selects the most optimal action
    def select_action(self, state):
        best_action, best_value = None, None
        for action in range(self.env.action_space.n):
            action_value = self.calc_action_value(state,action)
            if best_value is None or best_value < action_value:
                best_value = action_value
                best_action = action
        return best_action

    #Play one full episode using the provided environment with the best action
    def play_episode(self, env):
        total_reward = 0.0
        state = env.reset()
        while True:
            action = self.select_action(state)
            new_state, reward, is_done, extra_info = env.step(action)
            self.rewards[(state, action, new_state)] = reward
            self.transits[(state,action)][new_state] += 1
            total_reward += reward
            if is_done:
                break
            state = new_state
        return total_reward

    #Actual value iteration
    #Loops through all state in environment and for every state we calculate the values for the
    # states reachable from it, we then update the value of our state with the max value of action
    # available from the state        
    def value_iteration(self):
        for state in range(self.env.observation_space.n):
            state_values = [self.calc_action_value(state, action)
                            for action in range(self.env.action_space.n)]

            self.values[state] = max(state_values)


if __name__ == "__main__":
    test_env = gym.make(ENV_NAME)
    agent = Agent()
    writer = SummaryWriter(comment= "-v-iteration")

    iter_no = 0
    best_reward = 0.0

    while True:
        iter_no += 1
        #Training, perform 100 random steps to fill transition table with fresh data
        #Run iteration over all states
        agent.play_n_random_steps(100)
        agent.value_iteration()

        #Plays test episodes and writes data into tensorboard
        #Tracks best average reward and checks when to stop training
        reward = 0.0

        reward = 0.0
        for _ in range(TEST_EPISODES):
            reward += agent.play_episode(test_env)
        reward /= TEST_EPISODES
        writer.add_scalar("reward", reward, iter_no)
        if reward > best_reward:
            print("Best reward updated %.3f -> %.3f" % (best_reward, reward))
            best_reward = reward
        if reward > 0.80:
            print("Solved in %d iterations!" % iter_no)
            break
    writer.close()

    
