from runner import run_three_agents

sample_code = """
def get_user(id):
    query = "SELECT * FROM users WHERE id = " + id
    result = db.execute(query)
    return result
"""

sec, perf, style = run_three_agents(sample_code)
print("=== SECURITY ===")
print(sec[:500])
print("=== PERFORMANCE ===")
print(perf[:500])
print("=== STYLE ===")
print(style[:500])