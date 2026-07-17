from tasks import daily_update

if __name__ == "__main__":
    result = daily_update.delay()
    print(f"Workflow Submitted: {result.id}")