from storage import Storage

s = Storage()
print('Before sessions:', len(s.sessions))
s.clear_all_sessions()
print('Cleared sessions. After sessions:', len(s.sessions))
