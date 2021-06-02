import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))


    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]

        MP = 1
        SP = 0
        
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.sp_leftover = 0
        self.left_removed  = False
        self.right_removed = False
        self.full_defence = False
        self.just_attacked = False
        self.line = 0
        self.need_rebuild = {}
        self.prev_line=0
        self.ready_to_fire =False 
        
        global ourlocations
        ourlocations =  [[i,j] for i in range(14) for j in range(13-i,13+i+2)]


    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        attack_rounds = list(range(6,102,3))
        

   
        
       
        if game_state.turn_number < 101:
            self.rebuilding(game_state)
            self.remove_damaged(game_state, ourlocations, 20)
            
            if self.line==0:
                self.best_line_location(game_state)
                if self.ready_to_fire:                   
                    self.default_attack(game_state)
                self.default_opening_defence(game_state, attack_rounds)
                self.remove_line(game_state)
            else:
                self.demolishing_defence(game_state)
                self.demolisher_attack(game_state)
                self.best_line_location(game_state)
                self.remove_line(game_state)
        elif (self.left_removed==True) & (self.just_attacked==False):
            self.attack_left(game_state)
            self.defend_right(game_state)
            
        elif (self.left_removed==True) & (self.just_attacked==True):
            self.build_defences(game_state)
            self.left_removed=False
            self.just_attacked= False
        elif (self.right_removed==True) & (self.just_attacked==False):
            self.attack_right(game_state)
            self.defend_left(game_state)
            
        elif (self.right_removed==True) & (self.just_attacked==True):
            self.build_defences(game_state)
            self.right_removed=False
            self.just_attacked= False
        elif (self.detect_enemy_unit(game_state, unit_type=None, valid_x=[[0,1]], valid_y=[14])==2):
            self.remove_left_defence(game_state)
            self.defend_right(game_state)
        elif (self.detect_enemy_unit(game_state, unit_type=None, valid_x=[26,27], valid_y=[14])==2) :
            self.remove_right_defence(game_state)
            self.defend_left(game_state)
        else:
            self.build_defences(game_state)
    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[11,5],[16,5]]
        wall_locations = [[0, 13],[27,13], [13, 4], [14, 4],[12, 5], [15, 5], [1, 12],[26,12], [2, 12],[25,12], [3, 12],[24,12],[4, 11]
                          ,[5, 10], [6, 9], [7, 8], [8, 7], [9, 6], [10, 6] ,[17, 6], [18, 6], [19, 7],[20, 8], [21, 9], [22, 10], [23, 11]]
        vital_wall_locations =  [[0, 13],[27,13], [13, 4], [14, 4],[12, 5], [15, 5]]
        non_vital_wall_locations = [[1, 12],[26,12], [2, 12],[25,12], [3, 12],[24,12],[4, 11],[5, 10], [6, 9], [7, 8], [8, 7], [9, 6], 
                                     [10, 6] ,[17, 6], [18, 6], [19, 7],[20, 8], [21, 9], [22, 10], [23, 11]]
        extra_wall_locations = [[11, 6],[16, 6]]
        non_essential_walls = [[3,11],[24,11]]
        extra_turret_locations = [[2,11],[25,11]]
        wallsforattack= [[25,13],[2,13]]
        
        game_state.attempt_remove(wallsforattack)
        game_state.attempt_spawn(TURRET, turret_locations) #4SP
        game_state.attempt_spawn(WALL, wall_locations) #30SP
        game_state.attempt_spawn(TURRET, extra_turret_locations) #34SP
        game_state.attempt_spawn(WALL, extra_wall_locations) #36SP
        game_state.attempt_spawn(WALL,non_essential_walls)
        game_state.attempt_upgrade(extra_turret_locations) #44SP
        game_state.attempt_upgrade(vital_wall_locations) #56SP
        game_state.attempt_upgrade(turret_locations) #64SP
        game_state.attempt_upgrade(extra_wall_locations) #68SP
        self.sp_leftover = game_state.get_resource(SP)
        if (self.sp_leftover>5):
            self.full_defence=True
        game_state.attempt_upgrade(non_essential_walls)
        game_state.attempt_upgrade(non_vital_wall_locations)
    
    def remove_left_defence(self,game_state):
        locations = [[0,13],[1,13],[1,12],[2,12],[2,11],[3,11]]
        
        #present = [self.detect_my_unit(game_state,valid_x=[point[0]],valid_y=[point[1]]) for point in locations]
        #if all(present):
        game_state.attempt_remove(locations)
        
        self.left_removed=True
    def remove_right_defence(self,game_state):
        locations = [[25,11],[26,13],[25,12],[26,12],[27,13],[24,11]]
       # if self.detect_my_unit(game_state,locations)==len(locations):
        game_state.attempt_remove(locations)
        
        self.right_removed=True
    def defend_right(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[11,5],[16,5]]
        wall_locations = [[27,13], [13, 4], [14, 4],[12, 5], [15, 5], [26,12], [25,12], [3, 12],[24,12],[4, 11]
                          ,[5, 10], [6, 9], [7, 8], [8, 7], [9, 6], [10, 6] ,[17, 6], [18, 6], [19, 7],[20, 8], [21, 9], [22, 10], [23, 11]]
        vital_wall_locations =  [[27,13], [13, 4], [14, 4],[12, 5], [15, 5]]
        non_vital_wall_locations = [[26,12],[25,12], [3, 12],[24,12],[4, 11],[5, 10], [6, 9], [7, 8], [8, 7], [9, 6], 
                                     [10, 6] ,[17, 6], [18, 6], [19, 7],[20, 8], [21, 9], [22, 10], [23, 11]]
        extra_wall_locations = [[11, 6],[16, 6]]
        non_essential_walls = [[24,11]]
        extra_turret_locations = [[25,11]]
        
        game_state.attempt_spawn(TURRET, turret_locations) #4SP
        game_state.attempt_spawn(WALL, wall_locations) #30SP
        
        game_state.attempt_spawn(TURRET, extra_turret_locations) #34SP
        game_state.attempt_spawn(WALL, extra_wall_locations) #36SP
        game_state.attempt_spawn(WALL, non_essential_walls)
        game_state.attempt_upgrade(extra_turret_locations) #44SP
        game_state.attempt_upgrade(vital_wall_locations) #56SP
        game_state.attempt_upgrade(turret_locations) #64SP
        game_state.attempt_upgrade(extra_wall_locations) #68SP        

    
    def defend_left(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[11,5],[16,5]]
        wall_locations = [[0, 13], [13, 4], [14, 4],[12, 5], [15, 5], [1, 12], [2, 12], [3, 12],[24,12],[4, 11]
                          ,[5, 10], [6, 9], [7, 8], [8, 7], [9, 6], [10, 6] ,[17, 6], [18, 6], [19, 7],[20, 8], [21, 9], [22, 10], [23, 11]]
        vital_wall_locations =  [[0, 13], [13, 4], [14, 4],[12, 5], [15, 5]]
        non_vital_wall_locations = [[1, 12],[26,12], [2, 12],[25,12], [3, 12],[24,12],[4, 11],[5, 10], [6, 9], [7, 8], [8, 7], [9, 6], 
                                     [10, 6] ,[17, 6], [18, 6], [19, 7],[20, 8], [21, 9], [22, 10], [23, 11]]
        extra_wall_locations = [[11, 6],[16, 6]]
        non_essential_walls = [[3,11]]
        extra_turret_locations = [[2,11]]
        
        game_state.attempt_spawn(TURRET, turret_locations) #4SP
        game_state.attempt_spawn(WALL, wall_locations) #30SP
        
        game_state.attempt_spawn(TURRET, extra_turret_locations) #34SP
        game_state.attempt_spawn(WALL, extra_wall_locations) #36SP
        game_state.attempt_upgrade(extra_turret_locations) #44SP
        game_state.attempt_upgrade(vital_wall_locations) #56SP
        game_state.attempt_upgrade(turret_locations) #64SP
        game_state.attempt_upgrade(extra_wall_locations) #68SP
        

    def attack_left(self,game_state):
        game_state.attempt_spawn(WALL, [2,13])
        demdamage = self.damage_to_interceptor([3,10],game_state)
        cornerhealth = self.get_defence_health(game_state,[0,14])
        if cornerhealth>0:
            numberinterceptor = math.ceil(200/40 +math.floor(demdamage/40))# assume suppoted wall
            #scoutdamage = self.damage_to_scout([14,0],game_state)
            game_state.attempt_spawn(INTERCEPTOR, [3, 10], numberinterceptor)
        Mp = game_state.get_resource(MP)
        game_state.attempt_spawn(SCOUT , [14, 0], math.floor(Mp))
        self.just_attacked=True    

     
    
    def attack_right(self,game_state):
        game_state.attempt_spawn(WALL, [25,13])
        demdamage = self.damage_to_interceptor([24,10],game_state)
        cornerhealth = self.get_defence_health(game_state,[27,14])
        numberinterceptor = math.ceil(cornerhealth/40 +math.floor(demdamage/40))
        #scoutdamage = self.damage_to_scout([13,0],game_state)
        Mp = game_state.get_resource(MP)
        game_state.attempt_spawn(INTERCEPTOR, [24, 10], numberinterceptor)
        game_state.attempt_spawn(SCOUT , [13, 0], math.floor(Mp-numberinterceptor))        
        self.just_attacked=True
 
      
    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def demolisher_attack(self,game_state):
        all_support_locations = [[4,9],[2,11],[5,9],[5,8],[6,9],[6,8],[7,8],[8,8],[6,7],[7,7], [8,7]  ]
        my_mob = game_state.get_resource(MP)
        enemy_mob = game_state.get_resource(MP,1)
        n_interceptors = min(math.floor(enemy_mob),2) 
        n_demolishers = math.floor((my_mob-n_interceptors)/3)
        damage = game_state.damage_dealt_mobile( [22,8], game_state,DEMOLISHER,n_demolishers,player_index=0)
        game_state.attempt_spawn(INTERCEPTOR, [22, 8], n_interceptors)      
        if damage>8:
            game_state.attempt_spawn(DEMOLISHER, [5, 8], n_demolishers)
            if (game_state.get_resource(0,0) >  0 ):
                game_state.attempt_spawn(SUPPORT,all_support_locations)
                game_state.attempt_upgrade(all_support_locations)
                game_state.attempt_remove(all_support_locations)
    def default_attack(self,game_state):
        if self.ready_to_fire:
            left_support_locations = [[4,9],[2,11],[5,9],[5,8],[6,9],[6,8],[7,8],[8,8],[6,7],[7,7], [8,7] ]
            right_support_locations = [[27-i[0],i[1]] for i in left_support_locations]
            my_mob = game_state.get_resource(MP)
            enemy_mob = game_state.get_resource(MP,1)
            n_interceptors = min(math.floor(enemy_mob),2)            
            n_demolishers = math.floor((my_mob-n_interceptors)/3)
            damage_left = game_state.damage_dealt_mobile( [3,10], game_state,DEMOLISHER,n_demolishers,player_index=0)
            damage_right = game_state.damage_dealt_mobile( [24,10], game_state,DEMOLISHER,n_demolishers,player_index=0)
            if damage_left>=damage_right:
                supports= left_support_locations
                launch_loc = [3,10]
                game_state.attempt_spawn(WALL, [24, 11], n_interceptors)
            else:
                supports = right_support_locations
                launch_loc = [24,10]
                game_state.attempt_spawn(WALL, [3, 11], n_interceptors)
            
            game_state.attempt_spawn(INTERCEPTOR, launch_loc, n_interceptors)
            game_state.attempt_spawn(DEMOLISHER, launch_loc, n_demolishers)
            if (game_state.get_resource(0,0) >  0 ):
                game_state.attempt_spawn(SUPPORT,supports)
                game_state.attempt_upgrade(supports)
                game_state.attempt_remove(supports)
            self.ready_to_fire=False
            
    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units    
 


    def detect_my_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):

        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 0 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        return True
        return False
    

        
    def best_line_location(self,game_state):
        self.prev_line = self.line
        if self.detect_enemy_unit(game_state, unit_type=None, valid_x=list(range(8,21)), valid_y=[14])>4:
            if self.line<11:
                self.line=11
                return
            elif self.detect_enemy_unit(game_state, unit_type=TURRET, valid_x=list(range(8,21)), valid_y=[14]) == 0:
                if self.line<12:
                    self.line=12
                    return
                elif self.detect_enemy_unit(game_state, unit_type=TURRET, valid_x=list(range(8,21)), valid_y=[15]) == 0:
                    self.line=13
                else:
                    if self.detect_enemy_unit(game_state, unit_type=TURRET, valid_x=list(range(8,21)), valid_y=[14]) == 0:
                        self.line=12
                    else:
                        self.line=11
        elif self.detect_enemy_unit(game_state, unit_type=None, valid_x=list(range(8,21)), valid_y=[14,15])>4:
            if self.line<12:
                    self.line=12
                    return
            elif self.detect_enemy_unit(game_state, unit_type=TURRET, valid_x=list(range(8,21)), valid_y=[15]) == 0:
                self.line=13
            else:
                self.line=12
        elif self.detect_enemy_unit(game_state, unit_type=None, valid_x=list(range(8,21)), valid_y=[14,15,16]) > 4:
            self.line=13
        else:
            self.line=0
    def remove_line(self,game_state):
        if self.prev_line!= self.line:
            if self.prev_line==0:
                game_state.attempt_remove(ourlocations)
            else:    
                line_start= (13-self.prev_line)+3
                Walls_loc = [[i,self.prev_line]for i in range(line_start,21)]
                game_state.attempt_remove(Walls_loc)
                turret_loc = [[i,self.prev_line-2] for i in [6,13,21,9,18,]]
                game_state.attempt_remove(turret_loc)
            self.turn_to_rebuild = game_state.turn_number+1
    def demolishing_defence(self,game_state):
        if self.line==0:
            return
        line_start= (13-self.line)+3
            
        Walls_loc_2 = [[0,13],[27,13],[26,13],[1,13],[2,13],[25,13],[3,12],[24,12],[4,11],[23,11]]
        game_state.attempt_spawn(WALL, Walls_loc_2)
        Walls_loc = [[i,self.line]for i in range(line_start,21)]
        game_state.attempt_spawn(WALL, Walls_loc)


        turret_loc= [[2,12],[25,12],[6,(self.line-2)],[13,(self.line-2)],[21,self.line-2]]
        game_state.attempt_spawn(TURRET, turret_loc)
        game_state.attempt_upgrade([[1,13],[6,self.line-2],[26,13]]) #wall, turret, wall
        game_state.attempt_spawn(TURRET, [9,(self.line-2)])
        game_state.attempt_upgrade([21,(self.line-2)]) #turret
        game_state.attempt_spawn(TURRET, [18,(self.line-2)])
        game_state.attempt_spawn(WALL, [[5,10],[22,10]]) 

        game_state.attempt_upgrade([[13,(self.line-2)],[2,12],[25,12],[9,(self.line-2)],[18,(self.line-2)]]) #turrets
        game_state.attempt_upgrade([[line_start,self.line],[line_start+1,self.line],[line_start+5,self.line],[line_start+10,self.line],[line_start+14,self.line],[20,self.line],[0,13],[27,13],[2,13],[25,13],[3,12],[24,12],[4,11]])
        game_state.attempt_spawn(TURRET, [[1,12],[2,11]])
        #game_state.attempt_spawn(WALL, [22,10])
        game_state.attempt_upgrade([[1,12],[2,11]])
                                         
                                         
        '''game_state.attempt_upgrade([[22,10],[5,10]])
                game_state.attempt_spawn(TURRET, [26,12])
                game_state.attempt_upgrade([1,12],[2,11],[26,12])
                game_state.attempt_spawn(TURRET, [[11,(line-2)]])
                game_state.attempt_upgrade([11,(line-2)])
                game_state.attempt_spawn(TURRET, [17,(line-2)])
                game_state.attempt_upgrade([17,(line-2)])      
                
                
                important_wall = [[1,13],[26,13]]
                important_turret = [[6,11],[13,11][21,11],[2,12],[25,12]]
                wall_left = [[3,12],[4,11],[5,10]]
                wall_right = [[27-i[0],i[1]] for i in wall_loc]
                wall_loc_order = [x for y in zip(wall_left,wall_right) for x in y]
                game_state.attempt_spawn(TURRET, turret_loc)
                game_state.attempt_spawn(WALL, [[3,12],[14,12]])
                game_state.attempt_upgrade(important_wall)
                game_state.attempt_upgrade(important_turret)
                game_state.attempt_spawn(WALL, wall_loc_order)
                
                game_state.attempt_spawn(SUPPORT,[3,11])
                game_state.attempt_upgrade([[0,13],[27,13],[3,11],[9,11],[14,13],[18,11],[7,13],[12,13],[17,13]])
                game_state.attempt_spawn(SUPPORT,[3,10])
                game_state.attempt_upgrade([[2,13],[25,13],[3,10],[3,12],[24,12]])
                game.state.attempt_spawn(TURRETS,[[1,12],[2,11],[26,12],[25,11]])
                game_state.attempt_upgrade([4,11],[5,10],[23,11],[22,10])
                game.state.attempt_spawn(TURRETS,[[11,11],[15,11]])
                #build and take up supports with every attack, build turrets in gap
            if line ==11:
                Walls_loc_2 = [[0,13],[27,13],[26,13],[1,13],[2,13],[25,13],[3,12],[24,12],[4,11],[23,11]]
                game_state.attempt_spawn(WALL, Walls_loc_2)            
                Walls_loc = [[i,line]for i in range(7,26)]
                game_state.attempt_spawn(WALL, Walls_loc)
                
                turret_loc= [[2,12],[25,12],[6,(line-2)],[13,(line-2)],[21,line-2]]
                game_state.attempt_spawn(TURRET, turret_loc)
                
                game_state.attempt_upgrade([[1,13],[6,line-2],[26,13]])
                game_state.attempt_spawn(TURRET, [9,(line-2)])
                game_state.attempt_upgrade([21,(line-2)])
                game_state.attempt_spawn(TURRET, [18,(line-2)])
               
                game_state.attempt_spawn(WALL, [5,10])
                                      
                game_state.attempt_upgrade([[13,(line-2)],[2,12],[25,12],[9,(9+n)],[18,(line-2)]])
                game_state.attempt_upgrade([[24,11],[25,11],[10,11],[15,11],[20,11],[0,13],[27,13],[2,13],[25,13],[3,12],[24,12],[4,11]])
                   
                game_state.attempt_spawn(TURRET, [[1,12],[2,11]])
                #game_state.attempt_spawn(WALL, [22,10])
                game_state.attempt_upgrade([[1,12],[2,11]])
                game_state.attempt_spawn(SUPPORT,[24,10])
                game_state.attempt_upgrade([[23,10],[5,11]])
                game_state.attempt_spawn(TURRET, [[26,12]])
                game_state.attempt_upgrade([24,10],[1,12],[2,11],[26,12])
                game_state.attempt_spawn(TURRET, [[11,(line-2)]])
                game_state.attempt_upgrade([11,(line-2)])
                game_state.attempt_spawn(TURRET, [17,(line-2)])
                game_state.attempt_upgrade([17,(line-2)])                                              
                                                   
                              
                #build and take up supports with every attack, build turrets in gap '''           
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))
                
              
    def damage_to_interceptor(self, location, game_state,player_index=0):
        """Gets the damage to a unit released from location

        Args:
            location: The location of release
            game_state: current game_state

        Returns:
            damage to mobile unit from enemy stationary units if unchanged

        """

        if not player_index == 0 and not player_index == 1:
            game_state._invalid_player_index(player_index)

        damage = 0
        max_range = 3.5
        #interpath = game_state.find_path_to_edge(location)
        #pathtocorner = [i for i in interpath if i[1]<=13]
        pathtocorner = [[3,10],[3,11],[2,11],[2,12],[1,12],[1,13]]
        for path_point in pathtocorner:
            possible_turrets= game_state.game_map.get_locations_in_range(path_point, max_range)
            for location_unit in possible_turrets:
                for unit in game_state.game_map[location_unit]:
                    if unit.damage_i > 0 and unit.player_index != player_index and game_state.game_map.distance_between_locations(path_point, location_unit) <= unit.attackRange:
                        damage = damage + 4*unit.damage_i #change 4 to 1/mobileunit.speed
        return damage 

    def damage_to_scout(self, location, game_state,player_index=0):
        """Gets the damage to a unit released from location

        Args:
            location: The location of release
            game_state: current game_state

        Returns:
            damage to mobile unit from enemy stationary units if unchanged

        """

        if not player_index == 0 and not player_index == 1:
            game_state._invalid_player_index(player_index)

        damage = 0
        max_range = 3.5

        scoutpath = game_state.find_path_to_edge(location)
        for path_point in scoutpath:
            possible_turrets= game_state.game_map.get_locations_in_range(path_point, max_range)
            for location_unit in possible_turrets:
                for unit in game_state.game_map[location_unit]:
                    if unit.damage_i > 0 and unit.player_index != player_index and game_state.game_map.distance_between_locations(path_point, location_unit) <= unit.attackRange:
                        damage = damage + unit.damage_i #change 4 to 1/mobileunit.speed
        return damage 

    def damage_to_interceptor(self, location, game_state,player_index=0):
        """Gets the damage to a unit released from location

        Args:
            location: The location of release
            game_state: current game_state

        Returns:
            damage to mobile unit from enemy stationary units if unchanged

        """

        if not player_index == 0 and not player_index == 1:
            game_state._invalid_player_index(player_index)

        damage = 0
        max_range = 3.5

        interpath = game_state.find_path_to_edge(location)
        for path_point in interpath:
            possible_turrets= game_state.game_map.get_locations_in_range(path_point, max_range)
            for location_unit in possible_turrets:
                for unit in game_state.game_map[location_unit]:
                    if unit.damage_i > 0 and unit.player_index != player_index and game_state.game_map.distance_between_locations(path_point, location_unit) <= unit.attackRange:
                        damage = damage + 2*unit.damage_i #change 4 to 1/mobileunit.speed
        return damage 



    def remove_damaged(self,game_state,all_locations,low_health_threshold):                                                                                                   
        for location in all_locations:
            for unit in game_state.game_map[location]:                                          
                if unit.player_index == 0 and unit.stationary and unit.health< low_health_threshold:
                    game_state.attempt_remove(location)
                    self.need_rebuild[(location[0],location[1]) ]= unit.unit_type 
        
    def rebuilding(self,game_state):
        if len(self.need_rebuild )>0:
            for loc,type_unit in self.need_rebuild.items():
                game_state.attempt_spawn(type_unit,[loc[0],loc[1]])
            self.need_rebuild  = {}
 
    def get_defence_health(self, game_state, location):
        if game_state.contains_stationary_unit(location):
            for unit in game_state.game_map[location]:
                if unit.stationary:
                    health = unit.health
                    return health 
        else:
            return 0
        
    def default_opening_attack(self, game_state, attack_rounds):
        """
        Initial attempt at an attack
        """
        interceptor_rounds = [0,1,2,8]
        
        inter_deploy_locations = [[5,8],[22,8]]
        
        
        attack_deploy_locations = [[3,10]]   # for left launch attacks
        mirr_attack = [[27-i[0],i[1]] for i in attack_deploy_locations] # for right launch attacks
        
        
        
        
        if game_state.turn_number in interceptor_rounds:

            #game_state.attempt_spawn(INTERCEPTOR, inter_deploy_locations[0],1)
            game_state.attempt_spawn(INTERCEPTOR, inter_deploy_locations[1],2)
        
        
                
            
        # try to counter their initial attack, does waste out MP we are trying to save up for DEMOLISHERS
        #check_rounds = [5,9,15,21,27,33,39,45,51,57,65,71,77,83,89,94,99]
        #if game_state.turn_number == 4:
            #game_state.attempt_spawn(INTERCEPTOR, inter_deploy_locations[1],2)
                
        
        elif game_state.turn_number in attack_rounds:
            
            
            # Attack from the left
            if ( self.detect_enemy_unit(game_state, unit_type=TURRET, valid_x=[0,1,2,3,4,5], valid_y=[14,15,16,17,18])  )   <=   ( self.detect_enemy_unit(game_state, unit_type=TURRET, valid_x=[22,23,24,25,26,27], valid_y=[14,15,16,17,18]) ):   # left attack

                #if (game_state.turn_number == 7) or (game_state.turn_number == 20) or (game_state.turn_number == 35):
                #game_state.attempt_spawn(DEMOLISHER, attack_deploy_locations[1], 100)
                #gamelib.debug_write("Got into DEMOLISHER launch")
                    
                #elif (game_state.turn_number == 30) or (game_state.turn_number == 25):
                game_state.attempt_spawn(DEMOLISHER, attack_deploy_locations,1000) 
                game_state.attempt_spawn(INTERCEPTOR, attack_deploy_locations,1000)
                gamelib.debug_write("Got into double launch left")
                    
                #else:
                #game_state.attempt_spawn(SCOUT, deploy_locations[1],4)
                #game_state.attempt_spawn(SCOUT, deploy_locations[2],1000)
                #gamelib.debug_write("Got into double SCOUT launch")
                
            # Attack from the right
            else:
                
                game_state.attempt_spawn(DEMOLISHER, mirr_attack,1000) 
                game_state.attempt_spawn(INTERCEPTOR, mirr_attack,1000)
                gamelib.debug_write("Got into double launch right")
    def default_opening_defence(self,game_state, attack_rounds):
        """
        Strat 2 defence if there were no enemy defence detected in the front and middle of the areana.
        
        Starting SP = 30,
        WALL = 1, Upgrade = 2
        Turret = 2, Upgrade = 4
        Support = 4, Upgrade = 4 -> 1 health prior to upgrade
        
        # Does the support health stack? YES
        
        30 opening SP points
                                                                                   
        Get 5 SP every round - additional SP for every point of health taken off enemy                                                                           
                                                                                   
        """
        
        
        # Should check the other teams front line too see if it would be a waste to put initial walls on the front line anywhere they have some defences.
        # Should do calculations on how many SPs are available to us then build optimal defences with what SPs we have
        all_turret_locations=[[2,13],[2,12],[25,12],[5,10],[6,10],[10,9],[14,10],[17,9],     [1,12],[25,13],       [26,12],     [21,10],[22,10]]
        
        extra_turrets = [[12,9],[16,9]]
        
        all_wall_locations=[[0,13],[1,13],[3,13],[4,10],[27,13],[26,13],[24,13],[7,10],[10,10],[13,10],[15,10],[17,10],       [8,9],     [9,10],      [11,10],[12,10],[16,10],       [18,10],      [23,10],      [24,12],[7,9],    [19,9],[18,10],[20,10],     [9,9],[18,9], [21,11],[6,11],[3,12] ]
        delete_walls=[[3,11]]#,      [24,11]]   # could potentially delete [3,12] and build a support their for extra health on MPs
        mirr_delete_walls = [[24,11]]
        extra_walls =[[4,13]]#,[5,13]]#,      [24,12],[23,12],22,13]
        
    
        all_support_locations = [[4,9],[2,11],[5,9],[5,8],[6,9],[6,8],[7,8],[8,8],[6,7],[7,7], [8,7]  ]
        
        #                                                                                                  Self desrtuct dips                   
        upgrade_locations = [[3,13],[24,13],     [6,10],     [14,10],   [21,10],[7,10],              [8,9],[9,10],[19,9],[18,10],          [7,9],[9,9],[18,9],         [0,13],[1,13],[26,13],      [27,13],     [10,9],[10,10],[18,9],[20,9],     [2,13],[25,13],[17,10],    [5,10]]#         ,[11,10],[18,10],[17,10],  [22,10],[5,10],  [18,9],[20,9],[16,10],[12,10],[15,10],[13,10]] # [2,13], [25,13 are high turrets that need to be stronger]
        
        
        safety_turrets = [[9,8],[18,8],[9,7],[18,7],[10,6],[17,6],[11,5],[16,5],[12,4],[15,4],[13,3],[14,3]]
        safety_walls = [[10,8],[17,8],[10,7],[17,7],[11,6],[16,6],[12,5],[15,5],[13,4],[14,4],[14,3],[15,3]]
        
        
        # rounds to repeat the opening code
        blank_rounds = [7,8,9] 
        if game_state.turn_number<10  and game_state.turn_number!=6 and game_state.turn_number!=9:
            game_state.attempt_spawn(INTERCEPTOR, [[5,8],[22,8]])
        
        
        
        if game_state.turn_number == 0:
            
            # Spawn in the structures and attempt upgrades
            game_state.attempt_spawn(TURRET, all_turret_locations[0:8])

            game_state.attempt_spawn(WALL, all_wall_locations[0:12])
            game_state.attempt_spawn(WALL, delete_walls)
            game_state.attempt_spawn(WALL, mirr_delete_walls)
            
            
        
        
        # Recieve 5 structure points a round + 1 point for each bit of damage done to other algo's health
        elif game_state.turn_number == 1:
              
            turret_locations = self.filter_blocked_locations(all_turret_locations[0:10], game_state)
            if turret_locations:
                game_state.attempt_spawn(TURRET, turret_locations)
            
            wall_locations = self.filter_blocked_locations(all_wall_locations[0:13], game_state)
            if wall_locations:
                game_state.attempt_spawn(WALL, wall_locations)
           
            game_state.attempt_spawn(WALL, delete_walls)
            
            
            
            
        elif game_state.turn_number == 2:
            
            turret_locations = self.filter_blocked_locations(all_turret_locations[0:11], game_state)
            if turret_locations:
                game_state.attempt_spawn(TURRET, turret_locations)
            
            wall_locations = self.filter_blocked_locations(all_wall_locations[0:14], game_state)
            if wall_locations:
                game_state.attempt_spawn(WALL, wall_locations)
           
            game_state.attempt_upgrade(upgrade_locations[0])
            
            
            
        elif game_state.turn_number == 3:
                           
            wall_locations = self.filter_blocked_locations(all_wall_locations[0:17], game_state)
            if wall_locations:
                game_state.attempt_spawn(WALL, wall_locations)
           
            game_state.attempt_upgrade(upgrade_locations[0:2])
            
            
        elif game_state.turn_number == 4:
                           
            #do I upgrade first or repair first?
            wall_locations = self.filter_blocked_locations(all_wall_locations[0:18], game_state)
            if wall_locations:
                game_state.attempt_spawn(WALL, wall_locations)
           
            game_state.attempt_upgrade(upgrade_locations[0:3])
            
            
        elif game_state.turn_number == 6:
                           
            #do I upgrade first or repair first?
            turret_locations = self.filter_blocked_locations(all_turret_locations[0:11], game_state)
            if turret_locations:
                game_state.attempt_spawn(TURRET, turret_locations)
                
            wall_locations = self.filter_blocked_locations(all_wall_locations[0:19], game_state)
            if wall_locations:
                game_state.attempt_spawn(WALL, wall_locations)
        
            
            
        # repair rounds  
        elif game_state.turn_number in blank_rounds:
            
            turret_locations = self.filter_blocked_locations(all_turret_locations[0:11], game_state)
            if turret_locations:
                game_state.attempt_spawn(TURRET, turret_locations)
            
            wall_locations = self.filter_blocked_locations(all_wall_locations[0:21], game_state) # Spawn all of walls possible
            if wall_locations:
                game_state.attempt_spawn(WALL, wall_locations) 
                
                
            game_state.attempt_spawn(WALL, delete_walls)
            game_state.attempt_spawn(WALL, mirr_delete_walls)
            
        
        
            
        # Prep before attack rounds  
        elif (game_state.turn_number + 1) in attack_rounds: 
            if game_state.turn_number == 5:
                # Just repair
                wall_locations = self.filter_blocked_locations(all_wall_locations[0:19], game_state)
                if wall_locations:
                    game_state.attempt_spawn(WALL, wall_locations)                        
                game_state.attempt_upgrade(upgrade_locations[0:4])
                game_state.attempt_remove(delete_walls) 
                game_state.attempt_remove(mirr_delete_walls)
                self.ready_to_fire=True
                
                    
            
            elif game_state.turn_number == 10:           
                game_state.attempt_spawn(TURRET, all_turret_locations[0:13])
                game_state.attempt_spawn(WALL, all_wall_locations[0:24])                   
                game_state.attempt_upgrade(upgrade_locations[0:6])
                game_state.attempt_remove(delete_walls) 
                mirr_delete_walls = [[27-i[0],i[1]] for i in delete_walls]
                game_state.attempt_remove(mirr_delete_walls)
                self.ready_to_fire==True
                 
                
               
                
            
            else:

                game_state.attempt_spawn(TURRET, all_turret_locations,)
                game_state.attempt_spawn(WALL, all_wall_locations)
                game_state.attempt_remove(delete_walls) 
                mirr_delete_walls = [[27-i[0],i[1]] for i in delete_walls]
                game_state.attempt_remove(mirr_delete_walls) 
                self.ready_to_fire=True
                game_state.attempt_upgrade(all_turret_locations) 
                game_state.attempt_upgrade(all_wall_locations) 
                    
                # if right corner has less turrets than left   -- Attack from right          
                #if ( self.detect_enemy_unit(game_state, unit_type=TURRET, valid_x=[22,23,24,25,26,27], valid_y=[14,15,16,17,18])  )   <   ( self.detect_enemy_unit(game_state, unit_type=TURRET, valid_x=[0,1,2,3,4,5], valid_y=[14,15,16,17,18]) ):

         
        
        
        
        
        #  Defence for attack rounds   
        elif game_state.turn_number in attack_rounds:# or (game_state.turn_number == 9) or (game_state.turn_number == 13) or (game_state.turn_number == 21): 
            game_state.attempt_spawn(WALL, all_wall_locations)
            game_state.attempt_spawn(WALL, extra_walls)
            game_state.attempt_spawn(TURRET, all_turret_locations)
            game_state.attempt_upgrade(upgrade_locations)
            game_state.attempt_upgrade(all_wall_locations)
            game_state.attempt_upgrade(all_turret_locations)
        #     if ( self.detect_enemy_unit(game_state, unit_type=TURRET, valid_x=[0,1,2,3,4,5,6,7], valid_y=[14,15,16,17,18])  )   <=   ( self.detect_enemy_unit(game_state, unit_type=TURRET, valid_x=[19,21,22,23,24,25,26,27], valid_y=[14,15,16,17,18]) ):   # left attack
                
        #         #game_state.attempt_spawn(WALL, extra_walls)
                
        #         game_state.attempt_spawn(SUPPORT, all_support_locations[0:2])
        #         game_state.attempt_upgrade(all_support_locations[0:2])
        #         game_state.attempt_upgrade(upgrade_locations)
                
                
        #         game_state.attempt_spawn(SUPPORT, all_support_locations)
        #         game_state.attempt_upgrade(all_support_locations)
                
                
                
        #         turret_locations = self.filter_blocked_locations(all_turret_locations, game_state)
        #         if turret_locations:
        #             game_state.attempt_spawn(TURRET, turret_locations)
                
        #         wall_locations = self.filter_blocked_locations(all_wall_locations, game_state)
        #         if wall_locations:
        #             game_state.attempt_spawn(WALL, wall_locations)
                      
                
        #         # Have to remove supports to make the algo dynamic to two sided attacks
        #         game_state.attempt_remove(all_support_locations)
                
            
            
        #     else:
        #         mirr_delete_walls = [[27-i[0],i[1]] for i in delete_walls]
        #         mirr_all_support_locations = [[27-i[0],i[1]] for i in all_support_locations]
        #         mirr_extra_walls = [[27-i[0],i[1]] for i in extra_walls]
                
                
        #         game_state.attempt_spawn(SUPPORT, mirr_all_support_locations[0:2])
        #         game_state.attempt_upgrade(upgrade_locations)
        #         game_state.attempt_upgrade(mirr_all_support_locations[0:2])
                
        #         game_state.attempt_spawn(SUPPORT, mirr_all_support_locations)
        #         game_state.attempt_upgrade(mirr_all_support_locations)
                
        #         game_state.attempt_spawn(WALL, mirr_extra_walls)
                
                
                
                
        #         turret_locations = self.filter_blocked_locations(all_turret_locations, game_state)
        #         if turret_locations:
        #             game_state.attempt_spawn(TURRET, turret_locations)
                
        #         wall_locations = self.filter_blocked_locations(all_wall_locations, game_state)
        #         if wall_locations:
        #             game_state.attempt_spawn(WALL, wall_locations)
                      
  
        #         game_state.attempt_spawn(SUPPORT, mirr_all_support_locations[0:2])
        #         game_state.attempt_upgrade(upgrade_locations)
        #         game_state.attempt_upgrade(mirr_all_support_locations[0:2])
                
        #         game_state.attempt_spawn(SUPPORT, mirr_all_support_locations)
        #         game_state.attempt_upgrade(mirr_all_support_locations)
                
                
        #         game_state.attempt_remove(mirr_all_support_locations)
        #         #game_state.attempt_remove(mirr_extra_walls)
            
        
            
        
        
        
            
        else:
            # I think upgrading is considered more important than rebuilding
            game_state.attempt_spawn(WALL, delete_walls)
            game_state.attempt_spawn(WALL, mirr_delete_walls)
            
            
            turret_locations = self.filter_blocked_locations(all_turret_locations, game_state)
            if turret_locations:
                game_state.attempt_spawn(TURRET, turret_locations)
                
            #game_state.attempt_spawn(TURRET,extra_turrets)
                
            # attempt to rebuild any damages
            wall_locations = self.filter_blocked_locations(all_wall_locations, game_state)
            if wall_locations:
                game_state.attempt_spawn(WALL, wall_locations) 
                
            # rebuild destroyed walls

            game_state.attempt_upgrade(upgrade_locations)
            
            game_state.attempt_upgrade(all_turret_locations)
            game_state.attempt_upgrade(all_wall_locations) 
            game_state.attempt_upgrade(extra_turrets)
            
            
            # Check this out, make sure it's okay
            # if (game_state.get_resource(0,0) >  0 ):
            #     game_state.attempt_spawn(SUPPORT,all_support_locations)
            #     game_state.attempt_upgrade(allsupportlocations)
            #     game_state.attempt_spawn(TURRET,extra_turrets)
            #     game_state.attempt_upgrade(extra_turrets)
                
            #     game_state.attempt_spawn(TURRET,safety_turrets[0:8])
            #     game_state.attempt_spawn(WALL,safety_walls[0:8])
                
            #     game_state.attempt_upgrade(safety_turrets[0:8])
            #     game_state.attempt_upgrade(safety_walls[0:8])
        

                    
                    
    
                       
                                                                                           


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()

