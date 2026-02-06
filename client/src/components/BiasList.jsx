import React from "react";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Divider from "@mui/material/Divider";
import ListItemText from "@mui/material/ListItemText";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import Avatar from "@mui/material/Avatar";
import Typography from "@mui/material/Typography";
import AnchorIcon from "@mui/icons-material/Anchor";
import BlurOnIcon from "@mui/icons-material/BlurOn";
import SearchIcon from "@mui/icons-material/Search";

export default function BiasList({ apophText = "", anchText = "", abductText = "" }) {
  return (
    <List sx={{ width: "100%", bgcolor: "background.paper", borderRadius: 1 }}>
      <ListItem alignItems="flex-start">
        <ListItemAvatar>
          <Avatar>
            <BlurOnIcon />
          </Avatar>
        </ListItemAvatar>
        <ListItemText
          primary="Apophenia"
          secondary={
            <Typography component="span" variant="body2" color="text.primary">
              {apophText || "—"}
            </Typography>
          }
        />
      </ListItem>
      <Divider variant="inset" component="li" />
      <ListItem alignItems="flex-start">
        <ListItemAvatar>
          <Avatar>
            <AnchorIcon />
          </Avatar>
        </ListItemAvatar>
        <ListItemText
          primary="Anchoring"
          secondary={
            <Typography component="span" variant="body2" color="text.primary">
              {anchText || "—"}
            </Typography>
          }
        />
      </ListItem>
      <Divider variant="inset" component="li" />
      <ListItem alignItems="flex-start">
        <ListItemAvatar>
          <Avatar>
            <SearchIcon />
          </Avatar>
        </ListItemAvatar>
        <ListItemText
          primary="Abductive Reasoning"
          secondary={
            <Typography component="span" variant="body2" color="text.primary">
              {abductText || "—"}
            </Typography>
          }
        />
      </ListItem>
    </List>
  );
}
