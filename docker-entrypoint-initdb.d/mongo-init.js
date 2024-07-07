print('Start #################################################################');

db = db.getSiblingDB('sessions');
db.createCollection("sessions")
db.createUser(
  {
    user: "Username",
    pwd: "Password",
    roles: [
      {
        role: "readWrite",
        db: "sessions",
        collection: "sessions"
      }
    ]
  }
);

print('END #################################################################');