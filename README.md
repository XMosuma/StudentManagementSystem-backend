# -StudentManagementSystem-backend

# virtual enviroment
python3 -m venv venv
source venv/bin/activate
 
sudo apt install uvicorn
# run the backend 
uvicorn main:app --reload