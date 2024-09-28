#  DODGERS
#  PHILLIES
#  BREWERS
#  PADRES
#  METS
#  BRAVES
#  DIAMONDBACKS
# YANKEES
#  GUARDIANS
#  ASTROS
#  ORIOLES
#  TIGERS
# ROYALS

def contains_team(teams_text):
    teams = [
        "DODGERS", "PHILLIES", "BREWERS", "PADRES", "METS", 
        "BRAVES", "DIAMONDBACKS", "YANKEES", "GUARDIANS", 
        "ASTROS", "ORIOLES", "TIGERS", "ROYALS"
    ]
    
    return any(team in teams_text for team in teams)

