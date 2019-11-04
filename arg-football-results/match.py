# Usa python3

class Match():
	def __init__(self, date, stadium, home, away, home_goals, away_goals):
		# Everything is a string, except for the date
		self.date = date
		self.stadium = stadium
		self.home = home
		self.away = away
		self.home_goals = home_goals
		self.away_goals = away_goals
		
	def __str__(self):
		return ",".join([self.home,
						 self.away,
						 self.home_goals + "-" + self.away_goals,
						 self.stadium,
						 str(self.date)])
	
	def __lt__ (self,other):
		if self.date == other.date:
			return self.home < other.home
		return self.date < other.date
		
