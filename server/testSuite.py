from trackingVehicle import AppTracking

# AppTracking().trackEmptyInRanges()
AppTracking().findVehicleId("54L-37810")



"""Thread timer stop"""
# import threading
# def call_function_with_interval(param1, param2):
#     if param1 == 0:
#         # Cancel all running threads
#         threading.Timer(0, threading._shutdown).start()
#         return

#     param1 -= 1
#     threading.Timer(0.1, call_function_with_interval, args=(param1, param2)).start()
#     print(f"Param1: {param1}, Param2: {param2}")

# # Example usage
# param1 = 10
# param2 = "Hello"

# # Start calling the function with the given parameters every 2 seconds
# call_function_with_interval(param1, param2)
