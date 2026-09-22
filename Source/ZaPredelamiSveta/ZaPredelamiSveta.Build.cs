// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class ZaPredelamiSveta : ModuleRules
{
	public ZaPredelamiSveta(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"AIModule",
			"StateTreeModule",
			"GameplayStateTreeModule",
			"UMG",
			"Slate"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { });

		PublicIncludePaths.AddRange(new string[] {
			"ZaPredelamiSveta",
			"ZaPredelamiSveta/Variant_Platforming",
			"ZaPredelamiSveta/Variant_Platforming/Animation",
			"ZaPredelamiSveta/Variant_Combat",
			"ZaPredelamiSveta/Variant_Combat/AI",
			"ZaPredelamiSveta/Variant_Combat/Animation",
			"ZaPredelamiSveta/Variant_Combat/Gameplay",
			"ZaPredelamiSveta/Variant_Combat/Interfaces",
			"ZaPredelamiSveta/Variant_Combat/UI",
			"ZaPredelamiSveta/Variant_SideScrolling",
			"ZaPredelamiSveta/Variant_SideScrolling/AI",
			"ZaPredelamiSveta/Variant_SideScrolling/Gameplay",
			"ZaPredelamiSveta/Variant_SideScrolling/Interfaces",
			"ZaPredelamiSveta/Variant_SideScrolling/UI"
		});

		// Uncomment if you are using Slate UI
		// PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore" });

		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
