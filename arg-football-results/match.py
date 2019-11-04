# Usa python3

class Match():
	def __init__(self, date, round_slot, stadium, home, away, home_goals, away_goals, domestic):
		# Everything is a string, except for the date
		self.date = date
		self.round_slot = round_slot
		self.stadium = stadium
		self.home = home
		self.away = away
		self.home_goals = home_goals
		self.away_goals = away_goals
		self.domestic = domestic
		
	def get_home_goals(self):
		return int(self.home_goals)
		
	def get_away_goals(self):
		return int(self.away_goals)
		
	def __str__(self):
		return ",".join([str(self.round_slot),
						 self.home,
						 self.away,
						 self.home_goals + "-" + self.away_goals,
						 self.stadium,
						 str(self.date),
						 str(self.domestic)])
	
	def __lt__ (self,other):
		if self.date == other.date:
			return self.home < other.home
		return self.date < other.date
		
