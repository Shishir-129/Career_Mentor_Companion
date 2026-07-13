import language_tool_python
#package which is a python wrapper around languageTool

tool = language_tool_python.LanguageTool('en-US')
#creates the tool object 

def compute_grammer_score(transcript: str) -> tuple[float,list[str]]:
    if not transcript or not transcript.strip():
        return 0.0, ['Empty transcript']

    matches = tool.check(transcript)
    print("DEBUG - raw matches:", matches)   # <-- add this

    errors = [f"{m.message}" for m in matches]

    word_count = len(transcript.split())
    error_rate = len(matches) / word_count if word_count else 0
    score = round(max(0, 100 - (error_rate * 100)), 2)

    return score, errors

if __name__ == "__main__":
    transcript = "He go to school every day."

    score,errors = compute_grammer_score(transcript)
    print("grammatical score",score)
    for e in errors:
        print(f" - {e}")
