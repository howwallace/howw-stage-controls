
public override void Run()
{
	rotary.Request(Command.MoveAbsolute, convertLaserHeightToData(143.6));
	writeLine(xAxis, yAxis, 0.20, 4.8, 0, WIDTH, 0, "line");
	
	/*
	PARALLEL LINES AT DIFFERENT SPEEDS
	for (double i = 0; i <= 7; i ++)
	{
		writeLine(xAxis, yAxis, i*0.04 + 0.2, 0, i*0.1, 5, i*0.1, "parallel");
		moveTo(xAxis, yAxis, 5, -5 - REGION_O_Y, false);
		moveTo(xAxis, yAxis, 0, -5 - REGION_O_Y, false);
	}
	*/
	
	/*
	PARALLEL LINES AT DIFFERENT FOCAL HEIGHTS
	double startx = 4.2;
	double endx = 9.0;
	for (int z = 0; z <= 6; z = z + 1)
	{
		rotary.Request(Command.MoveAbsolute, convertLaserHeightToData(144.0 - z/10.0));
		writeLine(xAxis, yAxis, 0.20, startx, z/10.0, endx, z/10.0, "line " + (z+1));
		moveTo(xAxis, yAxis, endx, -5 - REGION_O_Y, false);
		moveTo(xAxis, yAxis, startx, -5 - REGION_O_Y, false);
	}
	*/
	
	//wipeRegion(xAxis, yAxis, 5, 0, 0, WIDTH, HEIGHT, true, "wipe");
	
	//moveTo(xAxis, yAxis, WIDTH+4, -5 - REGION_O_Y, false);
	
	home(xAxis, yAxis, rotary);
	
	//moveToSafety(xAxis, yAxis);
	Console.Beep(440, 2000);
	
	xAxis.Request(Command.SetTargetSpeed, (int)convertSpeedToData(5));
	yAxis.Request(Command.SetTargetSpeed, (int)convertSpeedToData(5));
	
	
	/**************** FOR REFERENCE ****************/
	//moveTo(xAxis, yAxis, rotary, x, y, false);
	//writeLine(xAxis, yAxis, rotary, speed, sX, sY, eX, eY, "line");
	//writeParallelLines(xAxis, yAxis, rotary, speed, sX, sY, eX, eY, xGap, yG, n, true, "parallel");
	//writeParallelLines(xAxis, yAxis, rotary, speed, dspeed, sX, sY, eX, eY, xGap, yG, n, nPerSpeed, true, "parallel, delta speed");
	//writeParallelAngledLines(xAxis, yAxis, rotary, speed, sX, sY, length, angle, xGap, yGap, n, true, commandName);
	//writeCircle(xAxis, yAxis, rotary, speed, rad, cX, cY, "circle");
	//writePartCircle(xAxis, yAxis, rotary, speed, rad, cX, cY, start, end, "part circle");
	//writeSpiral(xAxis, yAxis, rotary, speed, rad, gap, cX, cY, turns, "spiral");
	//wipeRegion(xAxis, yAxis, s, x1, y1, x2, y2, vertical, "wipe");
	/***********************************************/
}

// angle measures (deg) correspond to unit circle
public void writeParallelAngledLines(Conversation xAxis, Conversation yAxis, double speed, double sX, double sY, double length, double angle, double xGap, double yGap, int n, bool conserveMiddle, string commandName)
{
	double rad = Math.PI * angle / 180;	
	writeParallelLines(xAxis, yAxis, speed, sX, sY, sX + Math.Cos(rad) * length, sY + Math.Sin(rad) * length, xGap, yGap, n, conserveMiddle, commandName);
}

// pretty sure yGap should always be negative to prevent crossing
// (sX, sY) and (eX, eY) represent start and end of leftmost line
// writeParallelLines(xAxis, yAxis, 0.12, 0, 0, 0, 1, 0.02, 0, 10, false, "parallel");
public void writeParallelLines(Conversation xAxis, Conversation yAxis, double speed, double sX, double sY, double eX, double eY, double xGap, double yG, int n, bool conserveMiddle, string commandName)
{
	double yGap = -Math.Abs(yG);
	
	for (int i = 0; i < n; i ++)
	{
		writeLine(xAxis, yAxis, speed, sX + xGap*i, sY + yGap*i, eX + xGap*i, eY + yGap*i, commandName + i);
		
		if (conserveMiddle)
		{
			moveTo(xAxis, yAxis, eX + xGap*(n - 0.5), eY + yGap*(n - 0.5), false);
			if (i < n - 1)
				moveTo(xAxis, yAxis, sX + xGap*(n - 0.5), sY + yGap*(n - 0.5), false);
		}
		else
		{
			moveTo(xAxis, yAxis, eX + xGap*(i + 0.5),	eY + yGap*(i + 0.5),	false);
			moveTo(xAxis, yAxis, eX + xGap*(i + 0.5),	sY + yGap*(i + 0.5),	false);
			if (i < n - 1)
				moveTo(xAxis, yAxis, sX + xGap*(i + 1),	sY + yGap*(i + 0.5),	false);
		}
	}
}

// pretty sure yGap should always be negative to prevent crossing
// (sX, sY) and (eX, eY) represent start and end of first (leftmost/bottommost) line
// writeParallelLines(xAxis, yAxis, 0.12, 0, 0, 0, 1, 0.02, 0, 10, true, "parallel");
public void writeParallelLines(Conversation xAxis, Conversation yAxis, double speed, double dspeed, double sX, double sY, double eX, double eY, double xGap, double yG, int speeds, int nPerSpeed, bool conserveMiddle, string commandName)
{
	double yGap = -Math.Abs(yG);
	
	for (int i = 0; i < speeds; i ++)
	{
		double adjustX = xGap * i * nPerSpeed + (nPerSpeed == 1 ? 0 : 1)*(0.7 * xGap * i);
		double adjustY = yGap * i * nPerSpeed + (nPerSpeed == 1 ? 0 : 1)*(0.7 * yGap * i);
		writeParallelLines(xAxis, yAxis, speed + i*dspeed, sX + adjustX, sY + adjustY, eX + adjustX, eY  + adjustY, xGap, yG, nPerSpeed, conserveMiddle, commandName + ": " + i + ", ");
	}
}

// takes stages (x then y), velocity (mm/s), and start coordinates (mm) as arguments (and string commandName for reference in output)
public void writeLine(Conversation xAxis, Conversation yAxis, double s, double sX, double sY, double eX, double eY, string commandName)
{
	if (commandName != "")
		Output.WriteLine("STARTING: " + commandName);

	moveTo(xAxis, yAxis, sX, sY, false);
	moveTo(xAxis, yAxis, s, eX, eY, false);
}

// takes stages (x then y), velocity (mm/s), radius, centerX, and centerY (mm) as arguments (and string commandName for reference in output)
// STARTS WRITING AT PI (LEFT, CLOCKWISE)
public void writeCircle(Conversation xAxis, Conversation yAxis, double s, double rad, double cX, double cY, string commandName)
{
	writePartCircle(xAxis, yAxis, s, rad, cX, cY, 0, 1, commandName);
}
// same as above but start and end take doubles representing fraction of whole circle (e.g., 0 to 1 would be whole circle)
public void writePartCircle(Conversation xAxis, Conversation yAxis, double s, double rad, double cX, double cY, double start, double end, string commandName)
{
	System.Diagnostics.Stopwatch timer = new System.Diagnostics.Stopwatch();
	int invertFactor = INVERT ? -1 : 1;
	
	double speed = convertSpeedToData(s);
	double radius = convertDistanceToData(rad);
	double centerX = convertXPositionToData(cX);
	double centerY = convertYPositionToData(cY);
	
	double f = s / (1000 * rad);		// (mstep/s) / (1000 * mstep) = 1 / ms
	double period = 1000 * 2*Math.PI*rad / s;			// in ms

	// haven't checked...
	double startX = centerX + radius * Math.Cos(start * 2*Math.PI);
	double startY = centerY + radius * Math.Sin(start * 2*Math.PI);
	
	moveTo(xAxis, yAxis, startX, startY, true);
	
	//Sleep(100);	// check if necessary by sending successive moveTo commands and seeing what happens
	
	Output.WriteLine("STARTING");
	timer.Start();
	
	for (int t = (int)(start * period) + DELTA_T; t <= (int)(end * period); t += DELTA_T)
	{
		double deltaX = radius * (Math.Cos(f * (double)(t)) - Math.Cos(f * (double)(t - DELTA_T)));
		double deltaY = radius * (Math.Sin(f * (double)(t)) - Math.Sin(f * (double)(t - DELTA_T)));
		
		int xSpeed = (int)(1000 * deltaX / (DELTA_T * 9.375));
		int ySpeed = (int)(1000 * deltaY / (DELTA_T * 9.375));
		double calcSpeed = Math.Sqrt(Math.Pow(xSpeed, 2) + Math.Pow(ySpeed, 2)) / MSTEP_VEL_PER_MM_VEL;
		
		//Output.WriteLine(commandName + ": " + ((int)((double)t / (double)(period) * 1000) / 10.0) + "%  \t" + calcSpeed);
		
		xAxis.Send(Command.MoveAtConstantSpeed, -invertFactor * xSpeed);
		yAxis.Send(Command.MoveAtConstantSpeed, -invertFactor * ySpeed);
		
		while(timer.ElapsedMilliseconds + (int)(start * period) < t) {
			Sleep(1);
		}
	}
	timer.Stop();
	xAxis.Send(Command.Stop);
	yAxis.Send(Command.Stop);
}

// FOR MOVING WITHOUT CHANGING POLARIZATION
public void moveTo(Conversation xAxis, Conversation yAxis, double x, double y, bool data)
{
	moveTo(xAxis, yAxis, DEFAULT_HOMING_SPEED, x, y, data);
}
public void moveTo(Conversation xAxis, Conversation yAxis, double s, double x, double y, bool data)
{
	double currX = (double)xAxis.Request(Command.ReturnCurrentPosition).Data;
	double currY = (double)yAxis.Request(Command.ReturnCurrentPosition).Data;
	
	double toX = data ? x : convertXPositionToData(x);
	double toY = data ? y : convertYPositionToData(y);
	
	double xDist = Math.Abs(toX - currX);
	double yDist = Math.Abs(toY - currY);
	double dist = Math.Sqrt(Math.Pow(xDist, 2) + Math.Pow(yDist, 2));
	
	if ((int)dist == 0)
		return;
	
	double xSpeed = convertSpeedToData(s * xDist / dist);
	double ySpeed = convertSpeedToData(s * yDist / dist);
	
	Sleep(100);
	
	if ((int)xSpeed > 0 && (int)ySpeed > 0)
	{
		xAxis.Request(Command.SetTargetSpeed, (int)xSpeed);
		yAxis.Request(Command.SetTargetSpeed, (int)ySpeed);
		
		var topic = xAxis.StartTopic();
		xAxis.Send(Command.MoveAbsolute, (int)toX, topic.MessageId);
		yAxis.Request(Command.MoveAbsolute, (int)toY);
		topic.Wait();
		topic.Validate();
	}
	else if ((int)xSpeed > 0)
	{
		xAxis.Request(Command.SetTargetSpeed, (int)xSpeed);
		xAxis.Request(Command.MoveAbsolute, (int)toX);
	}
	else if ((int)ySpeed > 0)
	{
		yAxis.Request(Command.SetTargetSpeed, (int)ySpeed);
		yAxis.Request(Command.MoveAbsolute, (int)toY);
	}
}

public double convertDataToDistance(double mstep)
{
	return mstep * MM_PER_MSTEP;
}
public double convertXPositionToData(double x)
{
	if (INVERT)
		return convertDistanceToData(TR_X + REGION_O_X + x);
	return convertDistanceToData(O_X - REGION_O_X - x);
}
public double convertYPositionToData(double y)
{
	if (INVERT)
		return convertDistanceToData(TR_Y + REGION_O_Y + y);
	return convertDistanceToData(O_Y - REGION_O_Y - y);
}
public double convertSpeedToData(double mmpers)
{
	return mmpers * MSTEP_VEL_PER_MM_VEL;
}
public double convertDataToSpeed(double mmpers)
{
	return mmpers / MSTEP_VEL_PER_MM_VEL;
}


public int convertDegreesToData(double deg)
{
	return (int)(deg * DATA_PER_DEG);
}
*/
public double convertDataToDegrees(double data)
{
	return data / DATA_PER_DEG;
}
public int convertDegSpeedToData(double deg)
{
	return (int)(deg * 6990.5);
}

public void wipe(Conversation xAxis, Conversation yAxis)
{
	home(xAxis, yAxis);
	wipeRegion(xAxis, yAxis, 5, 0, 0, WIDTH, HEIGHT, true, "wipe");
}

// takes stages (x then y), speed (mm/s), and start coordinates (mm) as arguments (and string commandName for reference in output)
public void wipeRegion(Conversation xAxis, Conversation yAxis, double s, double x1, double y1, double x2, double y2, bool vertical, string commandName)
{
	System.Diagnostics.Stopwatch timer = new System.Diagnostics.Stopwatch();
	
	double speed = convertSpeedToData(s);
	double sX = vertical ? Math.Min(x1, x2) : x1;
	double eX = vertical ? Math.Max(x1, x2) : x2;
	double sY = vertical ? y1 : Math.Min(y1, y2);
	double eY = vertical ? y2 : Math.Max(y1, y2);
	
	moveTo(xAxis, yAxis, sX, sY, false);

	xAxis.Request(Command.SetTargetSpeed, (int)speed);
	yAxis.Request(Command.SetTargetSpeed, (int)speed);
	
	int totalSteps = (int)(4/3 * (vertical ? (eX - sX) : (eY - sY)) / WIPE_GAP);
	
	//Sleep(100);
	
	Output.WriteLine("STARTING");
	timer.Start();
	
	if (vertical)
	{
		for (int step = 0; step <= totalSteps; step ++)
		{
			yAxis.Request(Command.MoveAbsolute, (int)convertYPositionToData(eY));
			xAxis.Request(Command.MoveAbsolute, (int)convertXPositionToData(sX + step * WIPE_GAP));
			yAxis.Request(Command.MoveAbsolute, (int)convertYPositionToData(sY));
			xAxis.Request(Command.MoveAbsolute, (int)convertXPositionToData(sX + step * WIPE_GAP + (WIPE_GAP / 2)));
			
			double percentComplete = 100 * step / (double)(totalSteps);
			double elapsedSecs = (double)timer.ElapsedMilliseconds / (1000.0);
			double totalSecsRemaining = (100 * elapsedSecs / percentComplete) - elapsedSecs;
			double secsRemaining = (int)totalSecsRemaining % 60;
			double minsRemaining = ((int)totalSecsRemaining - secsRemaining) / 60;
			
			Output.WriteLine(commandName + ": " + String.Format("{0:00.00}", percentComplete) + "%;  \t" + minsRemaining + ":" + (secsRemaining < 10 ? "0" : "") + secsRemaining + " remaining");
		}
	}
	else
	{
		for (int step = 0; step <= totalSteps; step ++)
		{
			xAxis.Request(Command.MoveAbsolute, (int)convertXPositionToData(eX));
			yAxis.Request(Command.MoveAbsolute, (int)convertYPositionToData(sY + step * WIPE_GAP));
			xAxis.Request(Command.MoveAbsolute, (int)convertXPositionToData(sX));
			yAxis.Request(Command.MoveAbsolute, (int)convertYPositionToData(sY + step * WIPE_GAP + (WIPE_GAP / 2)));
			
			Output.WriteLine(commandName + ": " + (100 * step / (double)(totalSteps)) + "%");
		}
	}
	
	timer.Stop();
}


public void home(Conversation xAxis, Conversation yAxis)
{
	xAxis.Request(Command.SetHomeSpeed, (int)convertSpeedToData(DEFAULT_HOMING_SPEED));
	yAxis.Request(Command.SetHomeSpeed, (int)convertSpeedToData(DEFAULT_HOMING_SPEED));

	var topic = xAxis.StartTopic();
	xAxis.Send(Command.Home, topic.MessageId);
	yAxis.Request(Command.Home);
	topic.Wait();
	topic.Validate();
}

public void home(Conversation xAxis, Conversation yAxis, Conversation rotary)
{
	xAxis.Request(Command.SetHomeSpeed, (int)convertSpeedToData(DEFAULT_HOMING_SPEED));
	yAxis.Request(Command.SetHomeSpeed, (int)convertSpeedToData(DEFAULT_HOMING_SPEED));

	var topic = rotary.StartTopic();
	rotary.Send(Command.Home, topic.MessageId);
	xAxis.Send(Command.Home);
	yAxis.Send(Command.Home);
	topic.Wait();
	topic.Validate();
}

public void moveToSafety(Conversation xAxis, Conversation yAxis)
{
	double currX = (double)xAxis.Request(Command.ReturnCurrentPosition).Data;
	double currY = (double)yAxis.Request(Command.ReturnCurrentPosition).Data;
	
	if (INVERT)
	{
		moveTo(xAxis, yAxis, 5, convertDataToDistance(currX) - TR_X - REGION_O_X, -5 - REGION_O_Y, false);
		moveTo(xAxis, yAxis, 5, -5 - REGION_O_X, -5 - REGION_O_Y, false);
	}
	else
	{
		moveTo(xAxis, yAxis, 5, 5 + WIDTH - REGION_O_X, convertDataToDistance(currY) - O_Y - REGION_O_Y, false);
		moveTo(xAxis, yAxis, 5, 5 + WIDTH - REGION_O_X, -5 - REGION_O_Y, false);
		moveTo(xAxis, yAxis, 5, -5 - REGION_O_X, -5 - REGION_O_Y, false);
		moveTo(xAxis, yAxis, 5, -5 - REGION_O_X, -REGION_O_Y, false);
	}
}
