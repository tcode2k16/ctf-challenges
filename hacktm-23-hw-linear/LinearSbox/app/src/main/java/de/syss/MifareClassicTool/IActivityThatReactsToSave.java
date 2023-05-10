package de.syss.MifareClassicTool;

public interface IActivityThatReactsToSave {

    /**
     * This method will be called after a successful save process.
     */
    void onSaveSuccessful();

    /**
     * This method will be called, if there was an error during the
     * save process or it the user hits "cancel" in the "file already exists"
     * dialog.
     */
    void onSaveFailure();
}