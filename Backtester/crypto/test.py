import bitfinex

# Initialize the api
api = bitfinex.api_v1()

# Select a trading pair
pair = 'btcusd'

# Get the current ticker data for the pair
api.ticker(pair)

# Get all available currency pairs
symbols = api.symbols()