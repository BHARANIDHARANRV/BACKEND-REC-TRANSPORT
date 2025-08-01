# Railway deployment entry point - Complete FastAPI app
import os
import sys
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status, Security, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, date as dt_date
from typing import Optional, List
import uuid
import json

# Import modules
try:
    from database import init_database, create_default_users, close_database
    from models import User, Driver, Passenger, Admin, Ride, KilometerEntry, FuelEntry, LeaveRequest, DriverAttendance, RideStatus, LeaveRequestStatus, Vehicle
    from config import settings
    from auth import get_password_hash, verify_password, create_access_token, get_current_user, get_current_admin, get_current_driver
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"🔍 Current working directory: {os.getcwd()}")
    print(f"🔍 Files in current directory: {list(Path('.').glob('*.py'))}")
    raise

# Create FastAPI app
app = FastAPI(title="RideShare API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    await init_database()
    await create_default_users()
    print("✅ MongoDB Atlas connected and ready!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    await close_database()

# Test endpoint
@app.get("/test")
async def test_endpoint():
    return {"message": "RecTransport API is working with MongoDB Atlas!", "status": "success"}

# Simple test endpoint for mobile app
@app.get("/mobile-test")
async def mobile_test():
    """Simple test endpoint for mobile app connectivity"""
    return {
        "status": "success",
        "message": "Mobile app can reach the server!",
        "timestamp": datetime.utcnow().isoformat(),
        "server": "RecTransport API"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "message": "RecTransport API is running",
        "timestamp": datetime.utcnow().isoformat()
    }

# Debug endpoints (no authentication required)
@app.get("/debug/data")
async def debug_data():
    """Debug endpoint to check all data without authentication"""
    try:
        # Get all users
        users = await User.find_all().to_list()
        drivers = await Driver.find_all().to_list()
        passengers = await Passenger.find_all().to_list()
        vehicles = await Vehicle.find_all().to_list()
        
        return {
            "status": "success",
            "data": {
                "users_count": len(users),
                "drivers_count": len(drivers),
                "passengers_count": len(passengers),
                "vehicles_count": len(vehicles),
                "users": [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users],
                "drivers": [{"id": d.id, "user_id": d.user_id, "vehicle_make": d.vehicle_make, "license_plate": d.license_plate} for d in drivers],
                "passengers": [{"id": p.id, "user_id": p.user_id} for p in passengers],
                "vehicles": [{"id": v.id, "vehicle_make": v.vehicle_make, "license_plate": v.license_plate} for v in vehicles]
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/users")
async def debug_users():
    """Get all users without authentication"""
    try:
        users = await User.find_all().to_list()
        return {
            "status": "success",
            "users": [
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone": user.phone,
                    "role": user.role,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
                for user in users
            ]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/users-simple")
async def debug_users_simple():
    """Get all users in simple format without authentication"""
    try:
        users = await User.find_all().to_list()
        return {
            "status": "success",
            "users": [
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone": user.phone,
                    "role": user.role
                }
                for user in users
            ]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/debug/drivers")
async def debug_drivers():
    """Get all drivers without authentication (for testing)"""
    try:
        print("🔍 Debug: Fetching all drivers...")
        drivers = await Driver.find_all().to_list()
        
        # Get user info for each driver
        driver_list = []
        for driver in drivers:
            try:
                user = await User.get(driver.user_id)
                driver_data = {
                    "id": str(driver.id),
                    "user_id": str(driver.user_id),
                    "user_name": user.name if user else "Unknown",
                    "user_email": user.email if user else "Unknown",
                    "user_phone": user.phone if user else "Unknown",
                    "vehicle_make": driver.vehicle_make,
                    "vehicle_model": driver.vehicle_model,
                    "vehicle_year": driver.vehicle_year,
                    "license_plate": driver.license_plate,
                    "vehicle_color": driver.vehicle_color,
                    "license_number": driver.license_number,
                    "license_expiry": driver.license_expiry.isoformat() if driver.license_expiry else None,
                    "rating": driver.rating,
                    "total_rides": driver.total_rides,
                    "current_km_reading": driver.current_km_reading,
                    "is_online": driver.is_online,
                    "created_at": getattr(driver, 'created_at', None),
                    "updated_at": getattr(driver, 'updated_at', None)
                }
                
                # Convert datetime objects to ISO format if they exist
                if driver_data["created_at"]:
                    driver_data["created_at"] = driver_data["created_at"].isoformat()
                if driver_data["updated_at"]:
                    driver_data["updated_at"] = driver_data["updated_at"].isoformat()
                
                driver_list.append(driver_data)
            except Exception as e:
                print(f"❌ Error processing driver {driver.id}: {e}")
                continue
        
        print(f"✅ Debug: Found {len(driver_list)} drivers")
        
        # Log online status summary
        online_count = sum(1 for driver in driver_list if driver.get("is_online", False))
        offline_count = len(driver_list) - online_count
        print(f"📊 Online drivers: {online_count}, Offline drivers: {offline_count}")
        
        return {"status": "success", "drivers": driver_list}
    except Exception as e:
        print(f"❌ Debug: Error fetching drivers: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/debug/vehicles")
async def debug_vehicles():
    """Get all vehicles without authentication (for testing)"""
    try:
        print("🔍 Debug: Fetching all vehicles...")
        
        # Get vehicles created directly
        vehicles = await Vehicle.find_all().to_list()
        vehicle_list = []
        
        for vehicle in vehicles:
            vehicle_data = {
                "id": str(vehicle.id),
                "vehicle_make": vehicle.vehicle_make,
                "vehicle_model": vehicle.vehicle_model,
                "vehicle_year": vehicle.vehicle_year,
                "license_plate": vehicle.license_plate,
                "vehicle_color": vehicle.vehicle_color,
                "license_number": vehicle.license_number,
                "license_expiry": vehicle.license_expiry.isoformat() if vehicle.license_expiry else None,
                "created_at": getattr(vehicle, 'created_at', None),
                "updated_at": getattr(vehicle, 'updated_at', None)
            }
            
            # Convert datetime objects to ISO format if they exist
            if vehicle_data["created_at"]:
                vehicle_data["created_at"] = vehicle_data["created_at"].isoformat()
            if vehicle_data["updated_at"]:
                vehicle_data["updated_at"] = vehicle_data["updated_at"].isoformat()
            
            vehicle_list.append(vehicle_data)
        
        # Get vehicles from drivers
        drivers = await Driver.find_all().to_list()
        for driver in drivers:
            if (driver.vehicle_make and driver.vehicle_model and 
                driver.license_plate and driver.vehicle_color):
                try:
                    user = await User.get(driver.user_id)
                    vehicle_data = {
                        "id": f"driver_{str(driver.id)}",
                        "driver_id": str(driver.id),
                        "driver_name": user.name if user else "Unknown",
                        "vehicle_make": driver.vehicle_make,
                        "vehicle_model": driver.vehicle_model,
                        "vehicle_year": driver.vehicle_year,
                        "license_plate": driver.license_plate,
                        "vehicle_color": driver.vehicle_color,
                        "license_number": driver.license_number,
                        "license_expiry": driver.license_expiry.isoformat() if driver.license_expiry else None,
                        "created_at": getattr(driver, 'created_at', None),
                        "updated_at": getattr(driver, 'updated_at', None)
                    }
                    
                    # Convert datetime objects to ISO format if they exist
                    if vehicle_data["created_at"]:
                        vehicle_data["created_at"] = vehicle_data["created_at"].isoformat()
                    if vehicle_data["updated_at"]:
                        vehicle_data["updated_at"] = vehicle_data["updated_at"].isoformat()
                    
                    vehicle_list.append(vehicle_data)
                except Exception as e:
                    print(f"❌ Error processing driver vehicle {driver.id}: {e}")
                    continue
        
        print(f"✅ Debug: Found {len(vehicle_list)} vehicles")
        return {"status": "success", "vehicles": vehicle_list}
    except Exception as e:
        print(f"❌ Debug: Error fetching vehicles: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/debug/rides")
async def debug_rides():
    """Get all rides without authentication (for testing)"""
    try:
        print("🔍 Debug: Fetching all rides...")
        rides = await Ride.find_all().to_list()
        
        print(f"✅ Debug: Found {len(rides)} rides")
        
        ride_list = []
        for ride in rides:
            ride_data = {
                "id": str(ride.id),
                "passenger_id": ride.passenger_id,
                "driver_id": ride.driver_id,
                "status": ride.status,
                "pickup_address": ride.pickup_address,
                "dropoff_address": ride.dropoff_address,
                "requested_at": ride.requested_at.isoformat() if ride.requested_at else None,
                "assigned_at": ride.assigned_at.isoformat() if ride.assigned_at else None,
                "picked_up_at": ride.picked_up_at.isoformat() if ride.picked_up_at else None,
                "completed_at": ride.completed_at.isoformat() if ride.completed_at else None,
                "distance": ride.distance,
                "start_km": ride.start_km,
                "end_km": ride.end_km
            }
            ride_list.append(ride_data)
        
        return {"status": "success", "rides": ride_list}
    except Exception as e:
        print(f"❌ Debug: Error fetching rides: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/debug/fuel-entries")
async def debug_fuel_entries():
    """Get all fuel entries without authentication (for testing)"""
    try:
        print("🔍 Debug: Fetching all fuel entries...")
        fuel_entries = await FuelEntry.find_all().to_list()
        
        # First, let's see what drivers exist
        print("🔍 Debug: Checking what drivers exist...")
        all_drivers = await Driver.find_all().to_list()
        print(f"🔍 Debug: Found {len(all_drivers)} drivers:")
        for driver in all_drivers:
            print(f"  - Driver ID: {driver.id}, User ID: {driver.user_id}")
        
        # Get unique driver IDs from fuel entries
        fuel_driver_ids = set([entry.driver_id for entry in fuel_entries])
        print(f"🔍 Debug: Fuel entries reference these driver IDs: {fuel_driver_ids}")
        
        # Check which driver IDs exist
        existing_driver_ids = set([driver.id for driver in all_drivers])
        missing_driver_ids = fuel_driver_ids - existing_driver_ids
        print(f"🔍 Debug: Missing driver IDs: {missing_driver_ids}")
        
        # Get driver info for each fuel entry
        fuel_list = []
        
        # First, get all available drivers to use as fallback
        all_drivers = await Driver.find_all().to_list()
        default_driver = all_drivers[0] if all_drivers else None
        default_user = None
        if default_driver:
            default_user = await User.find_one({"_id": default_driver.user_id})
        
        print(f"🔍 Debug: Found {len(all_drivers)} drivers, using default: {default_driver.id if default_driver else 'None'}")
        
        for entry in fuel_entries:
            try:
                print(f"🔍 Debug: Processing fuel entry {entry.id} with driver_id: {entry.driver_id}")
                
                driver = await Driver.find_one({"_id": entry.driver_id})
                print(f"🔍 Debug: Found driver: {driver.id if driver else 'None'}")
                
                user = None
                if driver:
                    user = await User.find_one({"_id": driver.user_id})
                    print(f"🔍 Debug: Found user: {user.name if user else 'None'}")
                else:
                    # If driver not found, use default driver
                    driver = default_driver
                    user = default_user
                    print(f"🔍 Debug: Using default driver: {driver.id if driver else 'None'}")
                
                fuel_data = {
                    "id": str(entry.id),
                    "driver_id": str(entry.driver_id),
                    "driver_name": user.name if user else "Unknown",
                    "vehicle_make": driver.vehicle_make if driver else "Unknown",
                    "license_plate": driver.license_plate if driver else "Unknown",
                    "fuel_amount": entry.amount,
                    "fuel_cost": entry.cost,
                    "fuel_station": entry.location,
                    "date": entry.date.isoformat() if entry.date else None
                }
                fuel_list.append(fuel_data)
            except Exception as e:
                print(f"❌ Error processing fuel entry {entry.id}: {e}")
                continue
        
        print(f"✅ Debug: Found {len(fuel_list)} fuel entries")
        return {"status": "success", "fuel_entries": fuel_list}
    except Exception as e:
        print(f"❌ Debug: Error fetching fuel entries: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/debug/fix-fuel-entries")
async def fix_fuel_entries():
    """Fix fuel entries by assigning them to valid drivers"""
    try:
        print("🔧 Debug: Starting fuel entries fix...")
        
        # Get all drivers
        all_drivers = await Driver.find_all().to_list()
        if not all_drivers:
            return {"status": "error", "message": "No drivers found in database"}
        
        # Get all fuel entries
        fuel_entries = await FuelEntry.find_all().to_list()
        if not fuel_entries:
            return {"status": "error", "message": "No fuel entries found"}
        
        print(f"🔧 Debug: Found {len(all_drivers)} drivers and {len(fuel_entries)} fuel entries")
        
        # Get the first driver ID to use as default
        default_driver_id = all_drivers[0].id
        print(f"🔧 Debug: Using default driver ID: {default_driver_id}")
        
        # Fix each fuel entry
        fixed_count = 0
        for entry in fuel_entries:
            try:
                # Check if the current driver_id exists
                driver_exists = await Driver.find_one({"_id": entry.driver_id})
                
                if not driver_exists:
                    print(f"🔧 Debug: Fixing fuel entry {entry.id} - assigning to driver {default_driver_id}")
                    # Update the fuel entry with a valid driver ID
                    entry.driver_id = default_driver_id
                    await entry.save()
                    fixed_count += 1
                else:
                    print(f"🔧 Debug: Fuel entry {entry.id} already has valid driver {entry.driver_id}")
                    
            except Exception as e:
                print(f"❌ Error fixing fuel entry {entry.id}: {e}")
                continue
        
        print(f"✅ Debug: Fixed {fixed_count} fuel entries")
        return {
            "status": "success", 
            "message": f"Fixed {fixed_count} fuel entries",
            "fixed_count": fixed_count,
            "total_entries": len(fuel_entries)
        }
        
    except Exception as e:
        print(f"❌ Debug: Error fixing fuel entries: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/debug/rides-with-details")
async def debug_get_rides_with_details():
    """Get all rides with passenger and driver details for admin"""
    try:
        # Fetch all rides
        rides = await Ride.find_all().to_list()
        
        # Collect all passenger and driver IDs
        passenger_ids = [ride.passenger_id for ride in rides if ride.passenger_id]
        driver_ids = [ride.driver_id for ride in rides if ride.driver_id]
        
        # Fetch passengers
        passengers = {p.id: p async for p in Passenger.find({"_id": {"$in": passenger_ids}})}
        
        # Fetch drivers
        drivers = {d.id: d async for d in Driver.find({"_id": {"$in": driver_ids}})}
        
        # Fetch all user IDs for passengers and drivers
        passenger_user_ids = [p.user_id for p in passengers.values()]
        driver_user_ids = [d.user_id for d in drivers.values()]
        all_user_ids = list(set(passenger_user_ids + driver_user_ids))
        
        # Fetch all users
        users = {str(u.id): u async for u in User.find({"_id": {"$in": all_user_ids}})}
        
        # Create response with full details
        ride_responses = []
        for ride in rides:
            passenger = passengers.get(ride.passenger_id)
            driver = drivers.get(ride.driver_id) if ride.driver_id else None
            
            passenger_user = None
            driver_user = None
            
            if passenger:
                passenger_user = users.get(str(passenger.user_id))
            if driver:
                driver_user = users.get(str(driver.user_id))
            
            # Create ride response with full details
            ride_response = {
                "id": str(ride.id),
                "passenger_id": ride.passenger_id,
                "driver_id": ride.driver_id,
                "status": ride.status,
                "pickup_latitude": ride.pickup_latitude,
                "pickup_longitude": ride.pickup_longitude,
                "pickup_address": ride.pickup_address,
                "dropoff_latitude": ride.dropoff_latitude,
                "dropoff_longitude": ride.dropoff_longitude,
                "dropoff_address": ride.dropoff_address,
                "requested_at": ride.requested_at.isoformat() if ride.requested_at else None,
                "assigned_at": ride.assigned_at.isoformat() if ride.assigned_at else None,
                "picked_up_at": ride.picked_up_at.isoformat() if ride.picked_up_at else None,
                "completed_at": ride.completed_at.isoformat() if ride.completed_at else None,
                "distance": ride.distance,
                "start_km": ride.start_km,
                "end_km": ride.end_km,
                "passenger": {
                    "id": str(passenger.id) if passenger else None,
                    "user_id": passenger.user_id if passenger else None,
                    "rating": passenger.rating if passenger else 0.0,
                    "total_rides": passenger.total_rides if passenger else 0,
                    "user": {
                        "id": str(passenger_user.id) if passenger_user else None,
                        "name": passenger_user.name if passenger_user else "Unknown",
                        "email": passenger_user.email if passenger_user else "No email",
                        "phone": passenger_user.phone if passenger_user else "No phone",
                        "role": passenger_user.role if passenger_user else "passenger",
                        "avatar": passenger_user.avatar if passenger_user else None,
                        "created_at": passenger_user.created_at.isoformat() if passenger_user and passenger_user.created_at else None,
                        "is_active": passenger_user.is_active if passenger_user else True
                    } if passenger_user else None
                } if passenger else None,
                "driver": {
                    "id": str(driver.id) if driver else None,
                    "user_id": driver.user_id if driver else None,
                    "vehicle_make": driver.vehicle_make if driver else None,
                    "vehicle_model": driver.vehicle_model if driver else None,
                    "license_plate": driver.license_plate if driver else None,
                    "is_online": driver.is_online if driver else False,
                    "user": {
                        "id": str(driver_user.id) if driver_user else None,
                        "name": driver_user.name if driver_user else "Unknown",
                        "email": driver_user.email if driver_user else "No email",
                        "phone": driver_user.phone if driver_user else "No phone",
                        "role": driver_user.role if driver_user else "driver",
                        "avatar": driver_user.avatar if driver_user else None,
                        "created_at": driver_user.created_at.isoformat() if driver_user and driver_user.created_at else None,
                        "is_active": driver_user.is_active if driver_user else True
                    } if driver_user else None
                } if driver else None
            }
            ride_responses.append(ride_response)
        
        return {
            "status": "success",
            "rides": ride_responses,
            "total": len(ride_responses)
        }
        
    except Exception as e:
        print(f"Error in debug_get_rides_with_details: {e}")
        return {
            "status": "error",
            "message": str(e),
            "rides": []
        }

# Authentication endpoints
@app.post("/auth/login")
async def login(user_credentials: dict):
    print(f"🔐 Login attempt for email: {user_credentials.get('email')}")
    
    user = await User.find_one({"email": user_credentials.get("email")})
    
    if not user:
        print(f"❌ User not found for email: {user_credentials.get('email')}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    print(f"✅ User found: {user.name} (role: {user.role})")
    
    if not verify_password(user_credentials.get("password"), user.password_hash):
        print(f"❌ Password verification failed for user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    print(f"✅ Password verified successfully for user: {user.email}")
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    print(f"🎉 Login successful for user: {user.name}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# User management endpoints (admin only)
@app.post("/users")
async def create_user(user_data: dict, current_user: User = Depends(get_current_admin)):
    """Create a new user (admin only)"""
    # Check if user with this email already exists
    existing_user = await User.find_one({"email": user_data.get("email")})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create new user
    new_user = User(
        name=user_data.get("name"),
        email=user_data.get("email"),
        phone=user_data.get("phone"),
        role=user_data.get("role"),
        password_hash=get_password_hash("password"),  # Default password
    )
    await new_user.insert()
    
    return new_user

@app.post("/drivers")
async def create_driver(driver_data: dict, current_user: User = Depends(get_current_admin)):
    """Create a new driver (admin only)"""
    # Check if user with this email already exists
    existing_user = await User.find_one({"email": driver_data.get("user", {}).get("email")})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create user first
    new_user = User(
        name=driver_data.get("user", {}).get("name"),
        email=driver_data.get("user", {}).get("email"),
        phone=driver_data.get("user", {}).get("phone"),
        role="driver",
        password_hash=get_password_hash("password"),  # Default password
    )
    await new_user.insert()
    
    # Create driver profile with default vehicle values
    driver_profile = await Driver.create_driver(
        user_id=new_user.id,
        license_number=driver_data.get("license_number"),
        license_expiry=driver_data.get("license_expiry"),
        # Default vehicle values (can be updated later)
        vehicle_make=driver_data.get("vehicle_make", "Not Specified"),
        vehicle_model=driver_data.get("vehicle_model", "Not Specified"),
        vehicle_year=driver_data.get("vehicle_year", 2024),
        license_plate=driver_data.get("license_plate", "Not Assigned"),
        vehicle_color=driver_data.get("vehicle_color", "Not Specified"),
        rating=driver_data.get("rating", 5.0),
        total_rides=driver_data.get("total_rides", 0),
        current_km_reading=driver_data.get("current_km_reading", 0)
    )
    
    return driver_profile

@app.post("/passengers")
async def create_passenger(passenger_data: dict, current_user: User = Depends(get_current_admin)):
    """Create a new passenger (admin only)"""
    # Check if user with this email already exists
    existing_user = await User.find_one({"email": passenger_data.get("user", {}).get("email")})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create user first
    new_user = User(
        name=passenger_data.get("user", {}).get("name"),
        email=passenger_data.get("user", {}).get("email"),
        phone=passenger_data.get("user", {}).get("phone"),
        role="passenger",
        password_hash=get_password_hash("password"),  # Default password
    )
    await new_user.insert()
    
    # Create passenger profile
    passenger_profile = Passenger(
        user_id=new_user.id,
        rating=passenger_data.get("rating", 5.0),
        total_rides=passenger_data.get("total_rides", 0)
    )
    await passenger_profile.insert()
    
    return passenger_profile

# Driver management endpoints
@app.get("/drivers")
async def get_all_drivers(current_user: User = Depends(get_current_admin)):
    """Get all drivers (admin only)"""
    drivers = await Driver.find_all().to_list()
    return drivers

@app.get("/passengers")
async def get_all_passengers(current_user: User = Depends(get_current_admin)):
    """Get all passengers (admin only)"""
    passengers = await Passenger.find_all().to_list()
    user_ids = [p.user_id for p in passengers]
    users = {str(u.id): u async for u in User.find({"_id": {"$in": user_ids}})}
    response = []
    for p in passengers:
        user = users.get(str(p.user_id))
        passenger_dict = p.dict()
        passenger_dict["user"] = user.dict() if user else None
        response.append(passenger_dict)
    return response

@app.get("/passengers/me")
async def get_current_passenger_profile(current_user: User = Depends(get_current_user)):
    """Get current passenger's profile (for passengers to find their profile ID)"""
    try:
        print(f"🔍 Passenger /me endpoint called for user: {current_user.id}, role: {current_user.role}")
        
        if current_user.role != "passenger":
            print(f"❌ User {current_user.id} is not a passenger (role: {current_user.role})")
            raise HTTPException(status_code=403, detail="Only passengers can access this endpoint")
        
        print(f"🔍 Looking for passenger with user_id: {current_user.id}")
        passenger = await Passenger.find_one({"user_id": current_user.id})
        
        if not passenger:
            print(f"❌ No passenger profile found for user_id: {current_user.id}")
            # Let's check if there are any passengers at all
            all_passengers = await Passenger.find_all().to_list()
            print(f"🔍 Total passengers in database: {len(all_passengers)}")
            for p in all_passengers:
                print(f"🔍 Passenger: {p.id}, user_id: {p.user_id}")
            raise HTTPException(status_code=404, detail="Passenger profile not found")
        
        print(f"✅ Found passenger profile: {passenger.id}")
        print(f"🔍 Passenger object structure: {passenger}")
        return {"status": "success", "passenger": passenger}
    except Exception as e:
        print(f"❌ Error in /passengers/me: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get passenger profile: {str(e)}")

@app.put("/drivers/me/status")
async def update_driver_status(
    request: Request,
    current_user: User = Depends(get_current_driver)
):
    """Update driver online/offline status"""
    try:
        print(f"🔍 Driver status update requested for user: {current_user.id}")
        
        driver = await Driver.find_one({"user_id": current_user.id})
        if not driver:
            print(f"❌ Driver profile not found for user: {current_user.id}")
            raise HTTPException(status_code=404, detail="Driver profile not found")
        
        # Try to get data from JSON body first
        try:
            body_data = await request.json()
            is_online = body_data.get("is_online", False)
            print(f"🔍 Status from JSON body: {is_online}")
        except:
            # If JSON parsing fails, try query parameters
            is_online = request.query_params.get("is_online", "false").lower() == "true"
            print(f"🔍 Status from query params: {is_online}")
        
        print(f"🔍 Updating driver {driver.id} status from {driver.is_online} to {is_online}")
        driver.is_online = is_online
        await driver.save()
        
        print(f"✅ Driver status updated successfully: {driver.is_online}")
        return {"status": "success", "message": "Driver status updated", "driver": driver}
    except Exception as e:
        print(f"❌ Error updating driver status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update driver status: {str(e)}")

@app.get("/drivers/me")
async def get_current_driver_profile(current_user: User = Depends(get_current_driver)):
    """Get current driver's profile"""
    try:
        driver = await Driver.find_one({"user_id": current_user.id})
        if not driver:
            raise HTTPException(status_code=404, detail="Driver profile not found")
        
        return {"status": "success", "driver": driver}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get driver profile: {str(e)}")

@app.post("/vehicles")
async def create_vehicle(vehicle_data: dict, current_user: User = Depends(get_current_admin)):
    """Create a new vehicle (admin only, not attached to a driver)"""
    print(f"🚗 Creating vehicle with data: {vehicle_data}")
    
    # Validate required fields
    required_fields = [
        "vehicle_make", "vehicle_model", "vehicle_year", "license_plate",
        "vehicle_color", "license_number", "license_expiry"
    ]
    for field in required_fields:
        if not vehicle_data.get(field):
            print(f"❌ Missing required field: {field}")
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Parse license_expiry to datetime
    license_expiry = vehicle_data["license_expiry"]
    if isinstance(license_expiry, str):
        try:
            license_expiry = datetime.strptime(license_expiry, "%d-%m-%Y")
            print(f"✅ Parsed license_expiry: {license_expiry}")
        except Exception as e:
            print(f"❌ Error parsing license_expiry: {e}")
            raise HTTPException(status_code=400, detail="license_expiry must be in DD-MM-YYYY format")
    
    try:
        vehicle = Vehicle(
            vehicle_make=vehicle_data["vehicle_make"],
            vehicle_model=vehicle_data["vehicle_model"],
            vehicle_year=int(vehicle_data["vehicle_year"]),
            license_plate=vehicle_data["license_plate"],
            vehicle_color=vehicle_data["vehicle_color"],
            license_number=vehicle_data["license_number"],
            license_expiry=license_expiry
        )
        await vehicle.insert()
        print(f"✅ Vehicle created successfully with ID: {vehicle.id}")
        return vehicle
    except Exception as e:
        print(f"❌ Error creating vehicle: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create vehicle: {str(e)}")

@app.get("/vehicles")
async def get_all_vehicles(current_user: User = Depends(get_current_admin)):
    """Get all vehicles (admin only) - includes both direct vehicles and driver vehicles"""
    # Vehicles created directly
    vehicles = await Vehicle.find_all().to_list()
    vehicle_list = [
        {
            "id": v.id,
            "vehicle_make": v.vehicle_make,
            "vehicle_model": v.vehicle_model,
            "vehicle_year": v.vehicle_year,
            "license_plate": v.license_plate,
            "vehicle_color": v.vehicle_color,
            "license_number": v.license_number,
            "license_expiry": v.license_expiry.isoformat() if v.license_expiry else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "updated_at": v.updated_at.isoformat() if v.updated_at else None
        }
        for v in vehicles
    ]
    # Vehicles attached to drivers
    drivers = await Driver.find_all().to_list()
    for driver in drivers:
        if (driver.vehicle_make and driver.vehicle_model and 
            driver.license_plate and driver.vehicle_color):
            vehicle_list.append({
                "id": str(driver.id),
                "vehicle_make": driver.vehicle_make,
                "vehicle_model": driver.vehicle_model,
                "vehicle_year": driver.vehicle_year,
                "license_plate": driver.license_plate,
                "vehicle_color": driver.vehicle_color,
                "license_number": driver.license_number,
                "license_expiry": driver.license_expiry.isoformat() if driver.license_expiry else None,
                "created_at": driver.created_at.isoformat() if hasattr(driver, 'created_at') and driver.created_at else None,
                "updated_at": driver.updated_at.isoformat() if hasattr(driver, 'updated_at') and driver.updated_at else None
            })
    return vehicle_list

# Fuel entries management
@app.get("/fuel-entries")
async def get_fuel_entries(current_user: User = Depends(get_current_admin)):
    """Get all fuel entries (admin only)"""
    try:
        fuel_entries = await FuelEntry.find_all().to_list()
        
        # Get driver info for each fuel entry
        fuel_list = []
        
        # First, get all available drivers to use as fallback
        all_drivers = await Driver.find_all().to_list()
        default_driver = all_drivers[0] if all_drivers else None
        default_user = None
        if default_driver:
            default_user = await User.find_one({"_id": default_driver.user_id})
        
        print(f"🔍 Found {len(all_drivers)} drivers, using default: {default_driver.id if default_driver else 'None'}")
        
        for entry in fuel_entries:
            try:
                print(f"🔍 Processing fuel entry {entry.id} with driver_id: {entry.driver_id}")
                
                # Use find_one instead of get for better MongoDB compatibility
                driver = await Driver.find_one({"_id": entry.driver_id})
                print(f"🔍 Found driver: {driver.id if driver else 'None'}")
                
                user = None
                if driver:
                    user = await User.find_one({"_id": driver.user_id})
                    print(f"🔍 Found user: {user.name if user else 'None'}")
                else:
                    # If driver not found, use default driver
                    driver = default_driver
                    user = default_user
                    print(f"🔍 Using default driver: {driver.id if driver else 'None'}")
                
                fuel_data = {
                    "id": str(entry.id),
                    "driver_id": str(entry.driver_id),
                    "driver_name": user.name if user else "Unknown",
                    "vehicle_make": driver.vehicle_make if driver else "Unknown",
                    "license_plate": driver.license_plate if driver else "Unknown",
                    "fuel_amount": entry.amount,
                    "fuel_cost": entry.cost,
                    "fuel_station": entry.location,
                    "date": entry.date.isoformat() if entry.date else None
                }
                fuel_list.append(fuel_data)
            except Exception as e:
                print(f"❌ Error processing fuel entry {entry.id}: {e}")
                continue
        
        return {"status": "success", "fuel_entries": fuel_list}
    except Exception as e:
        print(f"❌ Error fetching fuel entries: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/fuel-entries")
async def create_fuel_entry(fuel_data: dict, current_user: User = Depends(get_current_admin)):
    """Create a new fuel entry (admin only)"""
    try:
        # Validate required fields
        required_fields = ["driver_id", "fuel_amount", "fuel_cost"]
        for field in required_fields:
            if not fuel_data.get(field):
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Parse date if provided
        fuel_date = fuel_data.get("date")
        if fuel_date and isinstance(fuel_date, str):
            try:
                fuel_date = datetime.strptime(fuel_date, "%Y-%m-%d")
            except:
                fuel_date = datetime.utcnow()
        else:
            fuel_date = datetime.utcnow()
        
        fuel_entry = FuelEntry(
            driver_id=fuel_data["driver_id"],
            amount=float(fuel_data["fuel_amount"]),
            cost=float(fuel_data["fuel_cost"]),
            location=fuel_data.get("fuel_station", "Unknown"),
            date=fuel_date,
            added_by="admin",
            admin_id=current_user.id
        )
        await fuel_entry.insert()
        
        return {"status": "success", "fuel_entry": fuel_entry}
    except Exception as e:
        print(f"❌ Error creating fuel entry: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create fuel entry: {str(e)}")

@app.post("/fuel-entries/me")
async def create_my_fuel_entry(fuel_data: dict, current_user: User = Depends(get_current_driver)):
    """Create a new fuel entry for the current driver"""
    try:
        print(f"🔧 Creating fuel entry for driver: {current_user.id}")
        print(f"🔧 Fuel data received: {fuel_data}")
        
        # Validate required fields
        required_fields = ["amount", "cost", "location"]
        for field in required_fields:
            if not fuel_data.get(field):
                print(f"❌ Missing required field: {field}")
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Get the driver record for this user
        driver = await Driver.find_one({"user_id": current_user.id})
        if not driver:
            print(f"❌ Driver profile not found for user: {current_user.id}")
            raise HTTPException(status_code=404, detail="Driver profile not found")
        
        print(f"🔧 Found driver: {driver.id}")
        
        # Parse date if provided
        fuel_date = fuel_data.get("date")
        if fuel_date and isinstance(fuel_date, str):
            try:
                fuel_date = datetime.strptime(fuel_date, "%Y-%m-%d")
            except:
                fuel_date = datetime.utcnow()
        else:
            fuel_date = datetime.utcnow()
        
        fuel_entry = FuelEntry(
            driver_id=str(driver.id),
            amount=float(fuel_data["amount"]),
            cost=float(fuel_data["cost"]),
            location=fuel_data["location"],
            date=fuel_date,
            added_by="driver",
            admin_id=current_user.id
        )
        await fuel_entry.insert()
        
        print(f"✅ Fuel entry created successfully: {fuel_entry.id}")
        return {"status": "success", "fuel_entry": fuel_entry}
    except Exception as e:
        print(f"❌ Error creating fuel entry: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create fuel entry: {str(e)}")

# Ride management
@app.post("/rides")
async def create_ride(ride_data: dict):
    """Create a new ride"""
    new_ride = Ride(
        passenger_id=ride_data.get("passenger_id"),
        pickup_latitude=ride_data.get("pickup_latitude"),
        pickup_longitude=ride_data.get("pickup_longitude"),
        pickup_address=ride_data.get("pickup_address"),
        dropoff_latitude=ride_data.get("dropoff_latitude"),
        dropoff_longitude=ride_data.get("dropoff_longitude"),
        dropoff_address=ride_data.get("dropoff_address"),
        status=RideStatus.REQUESTED
    )
    await new_ride.insert()
    return new_ride

@app.get("/rides")
async def get_rides(passenger_id: Optional[str] = None, driver_id: Optional[str] = None):
    """Get rides with optional filters and populate driver and passenger info"""
    query = {}
    if passenger_id:
        query["passenger_id"] = passenger_id
    if driver_id:
        query["driver_id"] = driver_id

    rides = await Ride.find(query).to_list()

    # Collect all driver and passenger IDs
    driver_ids = [ride.driver_id for ride in rides if ride.driver_id]
    passenger_ids = [ride.passenger_id for ride in rides if ride.passenger_id]

    # Fetch drivers and passengers
    drivers = {d.id: d async for d in Driver.find({"_id": {"$in": driver_ids}})}
    passengers = {p.id: p async for p in Passenger.find({"_id": {"$in": passenger_ids}})}

    # Fetch all user IDs
    user_ids = [d.user_id for d in drivers.values()] + [p.user_id for p in passengers.values()]
    users = {str(u.id): u async for u in User.find({"_id": {"$in": user_ids}})}

    # Attach driver and passenger user info to each ride
    for ride in rides:
        driver = drivers.get(ride.driver_id)
        if driver:
            driver.user = users.get(str(driver.user_id))
            ride.driver = driver
        passenger = passengers.get(ride.passenger_id)
        if passenger:
            passenger.user = users.get(str(passenger.user_id))
            ride.passenger = passenger

    return rides

@app.get("/rides/pending")
async def get_pending_rides(current_user: User = Depends(get_current_admin)):
    """Get all pending rides (admin only)"""
    rides = await Ride.find({"status": RideStatus.REQUESTED}).to_list()
    return rides

@app.get("/rides/assigned")
async def get_assigned_rides(current_user: User = Depends(get_current_driver)):
    """Get rides assigned to current driver"""
    # First, find the driver record for this user
    driver = await Driver.find_one({"user_id": current_user.id})
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    
    # Now use the driver.id to find rides
    rides = await Ride.find({"driver_id": driver.id, "status": {"$in": [RideStatus.ASSIGNED, RideStatus.IN_PROGRESS]}}).to_list()
    
    # Collect all passenger IDs
    passenger_ids = [ride.passenger_id for ride in rides if ride.passenger_id]
    
    # Fetch passengers using _id field
    passengers = {p.id: p async for p in Passenger.find({"_id": {"$in": passenger_ids}})}
    
    # Fetch all user IDs for passengers
    user_ids = [p.user_id for p in passengers.values()]
    users = {str(u.id): u async for u in User.find({"_id": {"$in": user_ids}})}
    
    # Create response with proper passenger structure
    ride_responses = []
    for ride in rides:
        passenger = passengers.get(ride.passenger_id)
        passenger_user = None
        if passenger:
            passenger_user = users.get(str(passenger.user_id))
        
        # Create ride response with passenger details
        ride_response = {
            "id": str(ride.id),
            "passenger_id": ride.passenger_id,
            "driver_id": ride.driver_id,
            "status": ride.status,
            "pickup_latitude": ride.pickup_latitude,
            "pickup_longitude": ride.pickup_longitude,
            "pickup_address": ride.pickup_address,
            "dropoff_latitude": ride.dropoff_latitude,
            "dropoff_longitude": ride.dropoff_longitude,
            "dropoff_address": ride.dropoff_address,
            "requested_at": ride.requested_at.isoformat() if ride.requested_at else None,
            "assigned_at": ride.assigned_at.isoformat() if ride.assigned_at else None,
            "picked_up_at": ride.picked_up_at.isoformat() if ride.picked_up_at else None,
            "completed_at": ride.completed_at.isoformat() if ride.completed_at else None,
            "distance": ride.distance,
            "start_km": ride.start_km,
            "end_km": ride.end_km,
            "passenger": {
                "id": str(passenger.id) if passenger else None,
                "user_id": passenger.user_id if passenger else None,
                "rating": passenger.rating if passenger else 0.0,
                "total_rides": passenger.total_rides if passenger else 0,
                "user": {
                    "id": str(passenger_user.id) if passenger_user else None,
                    "name": passenger_user.name if passenger_user else "Unknown",
                    "email": passenger_user.email if passenger_user else "No email",
                    "phone": passenger_user.phone if passenger_user else "No phone",
                    "role": passenger_user.role if passenger_user else "passenger",
                    "avatar": passenger_user.avatar if passenger_user else None,
                    "created_at": passenger_user.created_at.isoformat() if passenger_user and passenger_user.created_at else None,
                    "is_active": passenger_user.is_active if passenger_user else True
                } if passenger_user else None
            } if passenger else None
        }
        ride_responses.append(ride_response)
    
    return ride_responses

@app.post("/rides/{ride_id}/assign")
async def assign_ride_to_driver(ride_id: str, driver_id: str, current_user: User = Depends(get_current_admin)):
    """Assign a ride to a driver (admin only)"""
    try:
        ride = await Ride.get(ride_id)
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        driver = await Driver.get(driver_id)
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        ride.driver_id = driver_id
        ride.status = RideStatus.ASSIGNED
        ride.assigned_at = datetime.utcnow()
        await ride.save()
        
        return {"status": "success", "message": "Ride assigned successfully", "ride": ride}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign ride: {str(e)}")

@app.post("/rides/manual")
async def create_ride_manual(ride_data: dict, current_user: User = Depends(get_current_admin)):
    """Create a ride manually with driver assignment (admin only)"""
    try:
        # Create the ride
        new_ride = Ride(
            passenger_id=ride_data.get("passenger_id"),
            driver_id=ride_data.get("driver_id"),
            pickup_latitude=ride_data.get("pickup_latitude"),
            pickup_longitude=ride_data.get("pickup_longitude"),
            pickup_address=ride_data.get("pickup_address"),
            dropoff_latitude=ride_data.get("dropoff_latitude"),
            dropoff_longitude=ride_data.get("dropoff_longitude"),
            dropoff_address=ride_data.get("dropoff_address"),
            status=RideStatus.ASSIGNED if ride_data.get("driver_id") else RideStatus.REQUESTED,
            assigned_at=datetime.utcnow() if ride_data.get("driver_id") else None
        )
        await new_ride.insert()
        
        return {"status": "success", "ride": new_ride}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ride: {str(e)}")

@app.post("/rides/{ride_id}/start")
async def start_ride(ride_id: str, start_data: dict, current_user: User = Depends(get_current_driver)):
    """Start a ride (driver only)"""
    try:
        # Find the driver record for this user
        driver = await Driver.find_one({"user_id": current_user.id})
        if not driver:
            raise HTTPException(status_code=404, detail="Driver profile not found")
        
        ride = await Ride.get(ride_id)
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        if ride.driver_id != str(driver.id):
            raise HTTPException(status_code=403, detail="Not authorized to start this ride")
        
        ride.status = RideStatus.IN_PROGRESS
        ride.picked_up_at = datetime.utcnow()
        ride.start_km = start_data.get("start_km", 0)
        await ride.save()
        
        return {"status": "success", "message": "Ride started successfully", "ride": ride}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start ride: {str(e)}")

@app.post("/rides/{ride_id}/complete")
async def complete_ride(ride_id: str, complete_data: dict, current_user: User = Depends(get_current_driver)):
    """Complete a ride (driver only)"""
    try:
        # Find the driver record for this user
        driver = await Driver.find_one({"user_id": current_user.id})
        if not driver:
            raise HTTPException(status_code=404, detail="Driver profile not found")
        
        ride = await Ride.get(ride_id)
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        if ride.driver_id != str(driver.id):
            raise HTTPException(status_code=403, detail="Not authorized to complete this ride")
        
        ride.status = RideStatus.COMPLETED
        ride.completed_at = datetime.utcnow()
        ride.end_km = complete_data.get("end_km", 0)
        ride.distance = ride.end_km - ride.start_km if ride.start_km and ride.end_km else 0
        
        # Update driver's current km reading
        driver.current_km_reading = ride.end_km
        driver.total_rides += 1
        await driver.save()
        
        await ride.save()
        
        return {"status": "success", "message": "Ride completed successfully", "ride": ride}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete ride: {str(e)}")

# Attendance endpoints
@app.get("/attendance")
async def get_attendance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    driver_id: Optional[str] = None,
    current_user: User = Depends(get_current_admin)
):
    """Get attendance records (admin only)"""
    try:
        # Build query
        query = {}
        
        if driver_id:
            query["driver_id"] = driver_id
        
        if start_date:
            try:
                # Try to parse as ISO date
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query["date"] = {"$gte": start_dt}
            except:
                # Try to parse as DD-MM-YYYY
                try:
                    start_dt = datetime.strptime(start_date, "%d-%m-%Y")
                    query["date"] = {"$gte": start_dt}
                except:
                    pass
        
        if end_date:
            try:
                # Try to parse as ISO date
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                if "date" in query:
                    query["date"]["$lte"] = end_dt
                else:
                    query["date"] = {"$lte": end_dt}
            except:
                # Try to parse as DD-MM-YYYY
                try:
                    end_dt = datetime.strptime(end_date, "%d-%m-%Y")
                    if "date" in query:
                        query["date"]["$lte"] = end_dt
                    else:
                        query["date"] = {"$lte": end_dt}
                except:
                    pass
        
        print(f"🔍 Attendance query: {query}")
        
        # Get attendance records
        attendance_records = await DriverAttendance.find(query).to_list()
        
        # Get driver info for each record
        attendance_list = []
        for record in attendance_records:
            try:
                driver = await Driver.find_one({"_id": record.driver_id})
                user = None
                if driver:
                    user = await User.find_one({"_id": driver.user_id})
                
                attendance_data = {
                    "id": str(record.id),
                    "driver_id": str(record.driver_id),
                    "driver_name": user.name if user else "Unknown",
                    "date": record.date.isoformat() if record.date else None,
                    "check_in_time": record.check_in.isoformat() if record.check_in else None,
                    "check_out_time": record.check_out.isoformat() if record.check_out else None,
                    "status": record.status,
                    "notes": record.notes if hasattr(record, 'notes') else None
                }
                attendance_list.append(attendance_data)
            except Exception as e:
                print(f"❌ Error processing attendance record {record.id}: {e}")
                continue
        
        return {
            "status": "success",
            "attendance": attendance_list,
            "total": len(attendance_list)
        }
    except Exception as e:
        print(f"❌ Error fetching attendance: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/attendance")
async def create_attendance(attendance_data: dict, current_user: User = Depends(get_current_admin)):
    """Create attendance record (admin only)"""
    try:
        # Validate required fields
        required_fields = ["driver_id", "date"]
        for field in required_fields:
            if field not in attendance_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Parse date
        try:
            if isinstance(attendance_data["date"], str):
                # Try to parse as ISO date
                try:
                    date_obj = datetime.fromisoformat(attendance_data["date"].replace('Z', '+00:00'))
                except:
                    # Try to parse as DD-MM-YYYY
                    date_obj = datetime.strptime(attendance_data["date"], "%d-%m-%Y")
            else:
                date_obj = attendance_data["date"]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
        
        # Create attendance record
        attendance = DriverAttendance(
            driver_id=attendance_data["driver_id"],
            date=date_obj,
            check_in=attendance_data.get("check_in_time"),
            check_out=attendance_data.get("check_out_time"),
            status=attendance_data.get("status", "present")
        )
        
        await attendance.insert()
        
        return {
            "status": "success",
            "message": "Attendance record created successfully",
            "attendance": {
                "id": str(attendance.id),
                "driver_id": str(attendance.driver_id),
                "date": attendance.date.isoformat() if attendance.date else None,
                "status": attendance.status
            }
        }
    except Exception as e:
        print(f"❌ Error creating attendance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/attendance/{attendance_id}")
async def update_attendance(
    attendance_id: str,
    attendance_data: dict,
    current_user: User = Depends(get_current_admin)
):
    """Update attendance record (admin only)"""
    try:
        attendance = await DriverAttendance.find_one({"_id": attendance_id})
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        
        # Update fields
        if "check_in_time" in attendance_data:
            attendance.check_in = attendance_data["check_in_time"]
        if "check_out_time" in attendance_data:
            attendance.check_out = attendance_data["check_out_time"]
        if "status" in attendance_data:
            attendance.status = attendance_data["status"]
        
        await attendance.save()
        
        return {
            "status": "success",
            "message": "Attendance record updated successfully",
            "attendance": {
                "id": str(attendance.id),
                "driver_id": str(attendance.driver_id),
                "date": attendance.date.isoformat() if attendance.date else None,
                "status": attendance.status
            }
        }
    except Exception as e:
        print(f"❌ Error updating attendance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/attendance/{attendance_id}")
async def delete_attendance(
    attendance_id: str,
    current_user: User = Depends(get_current_admin)
):
    """Delete attendance record (admin only)"""
    try:
        attendance = await DriverAttendance.find_one({"_id": attendance_id})
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        
        await attendance.delete()
        
        return {
            "status": "success",
            "message": "Attendance record deleted successfully"
        }
    except Exception as e:
        print(f"❌ Error deleting attendance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Debug attendance endpoint
@app.get("/debug/attendance")
async def debug_attendance():
    """Debug endpoint to get all attendance records without authentication"""
    try:
        attendance_records = await DriverAttendance.find_all().to_list()
        
        attendance_list = []
        for record in attendance_records:
            try:
                driver = await Driver.find_one({"_id": record.driver_id})
                user = None
                if driver:
                    user = await User.find_one({"_id": driver.user_id})
                
                attendance_data = {
                    "id": str(record.id),
                    "driver_id": str(record.driver_id),
                    "driver_name": user.name if user else "Unknown",
                    "date": record.date.isoformat() if record.date else None,
                    "check_in_time": record.check_in.isoformat() if record.check_in else None,
                    "check_out_time": record.check_out.isoformat() if record.check_out else None,
                    "status": record.status,
                    "notes": record.notes if hasattr(record, 'notes') else None
                }
                attendance_list.append(attendance_data)
            except Exception as e:
                print(f"❌ Error processing attendance record {record.id}: {e}")
                continue
        
        return {
            "status": "success",
            "attendance": attendance_list,
            "total": len(attendance_list)
        }
    except Exception as e:
        print(f"❌ Error fetching attendance: {e}")
        return {"status": "error", "message": str(e)}

# Debug endpoint to check user authentication
@app.get("/debug/user-auth")
async def debug_user_auth(current_user: User = Depends(get_current_user)):
    """Debug endpoint to check current user authentication and role"""
    try:
        print(f"🔍 Debug user-auth called for user: {current_user.id}")
        print(f"🔍 User role: {current_user.role}")
        print(f"🔍 User name: {current_user.name}")
        print(f"🔍 User email: {current_user.email}")
        
        # Check if user has corresponding profile
        if current_user.role == "passenger":
            passenger = await Passenger.find_one({"user_id": current_user.id})
            print(f"🔍 Passenger profile found: {passenger is not None}")
            if passenger:
                print(f"🔍 Passenger ID: {passenger.id}")
        elif current_user.role == "driver":
            driver = await Driver.find_one({"user_id": current_user.id})
            print(f"🔍 Driver profile found: {driver is not None}")
            if driver:
                print(f"🔍 Driver ID: {driver.id}")
        
        return {
            "status": "success",
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "role": current_user.role
            }
        }
    except Exception as e:
        print(f"❌ Error in debug user-auth: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/debug/create-admin")
async def debug_create_admin(admin_data: dict):
    """Create an admin user without authentication (for testing)"""
    try:
        print(f"🔧 Debug: Creating admin with data: {admin_data}")
        
        # Check if user with this email already exists
        existing_user = await User.find_one({"email": admin_data.get("email")})
        if existing_user:
            return {"status": "error", "message": "User with this email already exists"}
        
        # Create admin user
        new_user = User(
            name=admin_data.get("name", "Admin User"),
            email=admin_data.get("email"),
            phone=admin_data.get("phone", "+1234567890"),
            role="admin",
            password_hash=get_password_hash(admin_data.get("password", "password"))
        )
        await new_user.insert()
        
        # Create admin profile
        admin_profile = Admin(
            user_id=new_user.id,
            permissions=admin_data.get("permissions", '["view_all", "manage_drivers", "manage_rides", "manage_passengers"]')
        )
        await admin_profile.insert()
        
        print(f"✅ Debug: Admin created successfully - {new_user.name}")
        return {
            "status": "success",
            "message": "Admin created successfully!",
            "admin": {
                "id": admin_profile.id,
                "user_id": admin_profile.user_id,
                "user": {
                    "id": new_user.id,
                    "name": new_user.name,
                    "email": new_user.email,
                    "role": new_user.role
                }
            }
        }
    except Exception as e:
        print(f"❌ Debug: Error creating admin: {e}")
        return {"status": "error", "message": str(e)}

# Debug passenger rides endpoint
@app.get("/debug/passenger-rides/{passenger_id}")
async def debug_passenger_rides(passenger_id: str):
    """Debug endpoint to get rides for a specific passenger without authentication"""
    try:
        print(f"🔍 Debug: Looking for rides with passenger_id: {passenger_id}")
        
        # Get all rides
        all_rides = await Ride.find_all().to_list()
        print(f"🔍 Debug: Found {len(all_rides)} total rides")
        
        # Filter rides for this passenger
        passenger_rides = [ride for ride in all_rides if str(ride.passenger_id) == passenger_id]
        print(f"🔍 Debug: Found {len(passenger_rides)} rides for passenger {passenger_id}")
        
        # Get passenger info
        passenger = await Passenger.find_one({"_id": passenger_id})
        passenger_user = None
        if passenger:
            passenger_user = await User.find_one({"_id": passenger.user_id})
            print(f"🔍 Debug: Passenger found - {passenger_user.name if passenger_user else 'Unknown'}")
            print(f"🔍 Debug: Passenger user_id: {passenger.user_id}")
            print(f"🔍 Debug: Passenger user found: {passenger_user is not None}")
        else:
            print(f"🔍 Debug: Passenger not found for ID: {passenger_id}")
            # Let's check all passengers to see what's available
            all_passengers = await Passenger.find_all().to_list()
            print(f"🔍 Debug: Total passengers in database: {len(all_passengers)}")
            for p in all_passengers:
                print(f"🔍 Debug: Available passenger: {p.id}, user_id: {p.user_id}")
        
        # Format rides for response
        rides_list = []
        for ride in passenger_rides:
            try:
                # Get driver info if assigned
                driver = None
                driver_user = None
                if ride.driver_id:
                    driver = await Driver.find_one({"_id": ride.driver_id})
                    if driver:
                        driver_user = await User.find_one({"_id": driver.user_id})
                
                ride_data = {
                    "id": str(ride.id),
                    "passenger_id": str(ride.passenger_id),
                    "driver_id": str(ride.driver_id) if ride.driver_id else None,
                    "status": ride.status.value if ride.status else "unknown",
                    "pickup_address": ride.pickup_address,
                    "dropoff_address": ride.dropoff_address,
                    "requested_at": ride.requested_at.isoformat() if ride.requested_at else None,
                    "assigned_at": ride.assigned_at.isoformat() if ride.assigned_at else None,
                    "picked_up_at": ride.picked_up_at.isoformat() if ride.picked_up_at else None,
                    "completed_at": ride.completed_at.isoformat() if ride.completed_at else None,
                    "distance": ride.distance,
                    "passenger": {
                        "id": str(passenger.id) if passenger else None,
                        "user": {
                            "id": str(passenger_user.id) if passenger_user else None,
                            "name": passenger_user.name if passenger_user else "Unknown",
                            "email": passenger_user.email if passenger_user else "No email"
                        }
                    },
                    "driver": {
                        "id": str(driver.id) if driver else None,
                        "user": {
                            "id": str(driver_user.id) if driver_user else None,
                            "name": driver_user.name if driver_user else "Unknown",
                            "email": driver_user.email if driver_user else "No email"
                        }
                    } if driver else None
                }
                rides_list.append(ride_data)
            except Exception as e:
                print(f"❌ Error processing ride {ride.id}: {e}")
                continue
        
        return {
            "status": "success",
            "passenger_id": passenger_id,
            "passenger_name": passenger_user.name if passenger_user else "Unknown",
            "rides": rides_list,
            "total": len(rides_list)
        }
    except Exception as e:
        print(f"❌ Error fetching passenger rides: {e}")
        return {"status": "error", "message": str(e)}

# Railway deployment
if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from Railway environment variable
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Starting RecTransport API server on port {port}")
    print(f"🔗 Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    print(f"📊 MongoDB URL: {os.environ.get('MONGODB_URL', 'Not set')[:50]}...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    ) 
